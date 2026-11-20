import unittest
from unittest import mock

from flask import Flask
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

from core.common import FILTERABLE_COLUMNS
from db.postgres_backend import _build_postgres_member_values
from routes.member_routes import create_member_blueprint


class MemberPasswordSyncTests(unittest.TestCase):
    def setUp(self):
        # The SQLite stand-in has no RBAC tables, and the account seed SQL is
        # PostgreSQL-only: record the membership hooks instead (CORE-35).
        self.seed_accounts = mock.patch('routes.member_routes.seed_member_accounts').start()
        self.sync_roles = mock.patch('routes.member_routes.sync_member_roles', return_value={'granted': 0, 'revoked': 0}).start()
        self.addCleanup(mock.patch.stopall)
        self.principal = None
        self.engine = create_engine('sqlite+pysqlite:///:memory:', future=True)
        self.session_factory = sessionmaker(bind=self.engine, future=True)
        metadata = MetaData()
        self.members_table = Table(
            'members',
            metadata,
            Column('id', Integer, primary_key=True),
            Column('club_id', Integer, nullable=False),
            Column('password', String, nullable=False),
            Column('email', String, nullable=False, default=''),
            Column('username', String, nullable=False, default=''),
        )
        self.app_users_table = Table(
            'app_users',
            metadata,
            Column('id', Integer, primary_key=True),
            Column('password_hash', String, nullable=False),
            Column('username', String, nullable=False, default=''),
        )
        self.links_table = Table(
            'member_user_links',
            metadata,
            Column('user_id', Integer, nullable=False),
            Column('member_id', Integer, nullable=False),
            Column('club_id', Integer, nullable=False),
        )
        metadata.create_all(self.engine)

        old_hash = generate_password_hash('old-password')
        with self.engine.begin() as connection:
            connection.execute(self.members_table.insert().values(
                id=10, club_id=1, password=old_hash, email='member@example.test'
            ))
            connection.execute(self.app_users_table.insert().values(
                id=20, password_hash=old_hash, username='old-name'
            ))
            connection.execute(self.app_users_table.insert().values(
                id=21, password_hash=old_hash, username='Taken'
            ))
            connection.execute(self.links_table.insert().values(
                user_id=20, member_id=10, club_id=1
            ))

        backend = {
            'session_factory': self.session_factory,
            'members_table': self.members_table,
            'app_users_table': self.app_users_table,
            'member_user_links_table': self.links_table,
        }
        deps = {
            'get_valid_club_short_names': lambda: ['CTC'],
            'log_database_target': lambda club: None,
            'get_read_db_for_club': lambda club: None,
            'get_db_for_club': lambda club: None,
            'get_column': lambda name, table: None,
            'get_identifier_column': lambda table: None,
            'member_to_dict': lambda member, table: {},
            'issue_member_token_pair': lambda *args, **kwargs: {},
            'load_member_roles': lambda *args, **kwargs: {},
            'extract_bearer_token': lambda: None,
            'revoke_member_session_token': lambda token: None,
            'revoke_member_refresh_token': lambda token: None,
            'get_member_refresh_session_from_token': lambda token: None,
            'get_current_principal': lambda *args, **kwargs: self.principal,
            'require_authenticated': lambda *args, **kwargs: None,
            'require_permission': lambda *args, **kwargs: None,
            'require_self_or_permission': lambda *args, **kwargs: None,
            'wildcard_to_sql_like': lambda value: value,
            'FILTERABLE_COLUMNS': FILTERABLE_COLUMNS,
            'is_postgres_writes_enabled': lambda: True,
            'get_postgres_backend': lambda: backend,
            '_resolve_postgres_club_id': lambda session, club: 1,
            '_build_postgres_member_values': _build_postgres_member_values,
        }
        app = Flask(__name__)
        app.register_blueprint(create_member_blueprint(deps))
        self.client = app.test_client()

    def tearDown(self):
        self.engine.dispose()

    def _stored_passwords(self):
        with self.session_factory() as session:
            member_password = session.execute(
                select(self.members_table.c.password).where(self.members_table.c.id == 10)
            ).scalar_one()
            app_user_password = session.execute(
                select(self.app_users_table.c.password_hash).where(self.app_users_table.c.id == 20)
            ).scalar_one()
            return member_password, app_user_password

    def test_password_change_updates_member_and_linked_app_user(self):
        response = self.client.put(
            '/members/10',
            json={'club': 'CTC', 'password': 'new-password'},
        )

        self.assertEqual(response.status_code, 200)
        member_password, app_user_password = self._stored_passwords()
        self.assertTrue(check_password_hash(member_password, 'new-password'))
        self.assertTrue(check_password_hash(app_user_password, 'new-password'))
        self.sync_roles.assert_called_once()  # CORE-35: membership re-derived on update

    def test_empty_password_does_not_clear_existing_passwords(self):
        response = self.client.put(
            '/members/10',
            json={'club': 'CTC', 'password': ''},
        )

        self.assertEqual(response.status_code, 200)
        member_password, app_user_password = self._stored_passwords()
        self.assertTrue(check_password_hash(member_password, 'old-password'))
        self.assertTrue(check_password_hash(app_user_password, 'old-password'))


    def _app_user_username(self, user_id=20):
        with self.session_factory() as session:
            return session.execute(
                select(self.app_users_table.c.username).where(self.app_users_table.c.id == user_id)
            ).scalar_one()

    def test_username_change_reaches_linked_app_user(self):
        self.principal = {'permissions': ['member.club.update']}  # username: admin edit (CORE-16)
        # CORE-35: app_users is the only login in PostgreSQL mode, so a
        # username set on the member record must reach the account.
        response = self.client.put('/members/10', json={'club': 'CTC', 'username': 'new-name'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._app_user_username(), 'new-name')

    def test_username_already_used_by_another_account_is_refused(self):
        self.principal = {'permissions': ['member.club.update']}  # username: admin edit (CORE-16)
        response = self.client.put('/members/10', json={'club': 'CTC', 'username': 'taken'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self._app_user_username(), 'old-name')
        with self.session_factory() as session:
            member_username = session.execute(
                select(self.members_table.c.username).where(self.members_table.c.id == 10)
            ).scalar_one()
        self.assertEqual(member_username, '')  # nothing saved

    def test_blank_username_leaves_account_alone(self):
        self.principal = {'permissions': ['member.club.update']}  # username: admin edit (CORE-16)
        response = self.client.put('/members/10', json={'club': 'CTC', 'username': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._app_user_username(), 'old-name')


if __name__ == '__main__':
    unittest.main()
