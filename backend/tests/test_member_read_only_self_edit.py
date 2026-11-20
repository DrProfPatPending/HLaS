import unittest
from unittest import mock

from flask import Flask
from sqlalchemy import BigInteger, Column, Integer, MetaData, String, Table, create_engine, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.postgres_backend import _build_postgres_member_values
from routes import member_routes
from routes.member_routes import create_member_blueprint

READ_ONLY_CONFIG = {'read_only': {'my_club': {'Member_Type': True, 'Paid_Up_2026': False}}}
MEMBER = {'permissions': ['member.self.read', 'member.self.update'], 'member_id': 7}
ADMIN = {'permissions': ['member.self.update', 'member.club.update'], 'member_id': 1}


class _Deps(dict):
    def __missing__(self, key):
        return mock.Mock(name=key)


def _memory_engine():
    return create_engine(
        'sqlite+pysqlite://', future=True,
        connect_args={'check_same_thread': False}, poolclass=StaticPool,
    )


def _client(principal, **overrides):
    deps = _Deps(
        require_self_or_permission=lambda member_id, permission, club=None: None,
        get_current_principal=lambda club=None: principal,
        log_database_target=lambda club: None,
        _build_postgres_member_values=_build_postgres_member_values,
        _resolve_postgres_club_id=lambda session, club: 1,
        is_postgres_reads_enabled=lambda: False,
        is_postgres_writes_enabled=lambda: False,
    )
    deps.update(overrides)
    app = Flask(__name__)
    app.register_blueprint(create_member_blueprint(deps))
    return app.test_client()


class ReadOnlySelfEditPostgresTests(unittest.TestCase):
    def setUp(self):
        # The SQLite stand-in has no RBAC tables, and the account seed SQL is
        # PostgreSQL-only: record the membership hooks instead (CORE-35).
        self.seed_accounts = mock.patch('routes.member_routes.seed_member_accounts').start()
        self.sync_roles = mock.patch('routes.member_routes.sync_member_roles', return_value={'granted': 0, 'revoked': 0}).start()
        self.addCleanup(mock.patch.stopall)
        engine = _memory_engine()
        self.addCleanup(engine.dispose)
        metadata = MetaData()
        self.members = Table(
            'members', metadata,
            Column('id', Integer, primary_key=True),
            Column('club_id', BigInteger, nullable=False),
            Column('number', String(64), nullable=False, server_default=''),
            Column('members_name', String(255), nullable=False, server_default=''),
            Column('member_type', String(120), nullable=False, server_default=''),
            Column('paid_up_2026', String(32), nullable=False, server_default=''),
        )
        metadata.create_all(engine)
        self.session_factory = sessionmaker(bind=engine, future=True)
        with self.session_factory() as session:
            session.execute(self.members.insert().values(
                id=7, club_id=1, number='42', members_name='Alex Archer', member_type='Ordinary', paid_up_2026='Y',
            ))
            session.commit()
        self.backend = {'session_factory': self.session_factory, 'members_table': self.members}
        patcher = mock.patch.object(member_routes, 'load_field_order_config', return_value=READ_ONLY_CONFIG)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _put(self, principal, payload):
        client = _client(
            principal,
            is_postgres_reads_enabled=lambda: True,
            is_postgres_writes_enabled=lambda: True,
            get_postgres_backend=lambda: self.backend,
        )
        return client.put('/members/7', json={'club': 'CTC', **payload})

    def _row(self):
        with self.session_factory() as session:
            return session.execute(select(self.members).where(self.members.c.id == 7)).one()._mapping

    def test_member_cannot_change_their_number(self):
        response = self._put(MEMBER, {'Number': '1', 'Members_Name': 'Alex A. Archer'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()['fields'], ['Number'])
        self.assertEqual(self._row()['number'], '42')
        self.assertEqual(self._row()['members_name'], 'Alex Archer', 'nothing is saved')

    def test_member_cannot_change_club_read_only_field(self):
        response = self._put(MEMBER, {'Member_Type': 'Honorary'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()['fields'], ['Member_Type'])
        self.assertEqual(self._row()['member_type'], 'Ordinary')

    def test_member_can_resend_unchanged_read_only_values_and_edit_others(self):
        response = self._put(MEMBER, {'Number': 42, 'Member_Type': 'Ordinary', 'Members_Name': 'Alex A. Archer'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._row()['members_name'], 'Alex A. Archer')

    def test_fields_not_marked_read_only_stay_editable(self):
        response = self._put(MEMBER, {'Paid_Up_2026': 'N'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._row()['paid_up_2026'], 'N')

    def test_admin_can_change_read_only_fields(self):
        response = self._put(ADMIN, {'Number': '1', 'Member_Type': 'Honorary'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual((self._row()['number'], self._row()['member_type']), ('1', 'Honorary'))


class ReadOnlySelfEditSqliteTests(unittest.TestCase):
    def setUp(self):
        engine = _memory_engine()
        self.addCleanup(engine.dispose)
        with engine.begin() as conn:
            conn.execute(text(
                'CREATE TABLE members (ID INTEGER PRIMARY KEY, Number TEXT, Members_Name TEXT, Member_Type TEXT)'
            ))
            conn.execute(text(
                "INSERT INTO members VALUES (7, '42', 'Alex Archer', 'Ordinary')"
            ))
        metadata = MetaData()
        metadata.reflect(bind=engine)
        self.members = metadata.tables['members']

        from sqlalchemy.ext.automap import automap_base
        base = automap_base(metadata=metadata)
        base.prepare()
        self.Member = base.classes.members
        self.session = sessionmaker(bind=engine, future=True)()
        self.addCleanup(self.session.close)
        patcher = mock.patch.object(member_routes, 'load_field_order_config', return_value=READ_ONLY_CONFIG)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _get_column(self, name, table):
        return next((column for column in table.columns if column.name.lower() == str(name).lower()), None)

    def _put(self, principal, payload):
        db_info = {'session': self.session, 'members_table': self.members, 'Member': self.Member}
        client = _client(principal, get_db_for_club=lambda club: db_info, get_column=self._get_column)
        return client.put('/members/7', json={'club': 'CTC', **payload})

    def _stored(self, column):
        return self.session.execute(text(f'SELECT {column} FROM members WHERE ID = 7')).scalar_one()

    def test_member_cannot_change_their_number(self):
        response = self._put(MEMBER, {'Number': '1'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self._stored('Number'), '42')

    def test_member_can_edit_other_fields(self):
        response = self._put(MEMBER, {'Number': '42', 'Members_Name': 'Alex A. Archer'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._stored('Members_Name'), 'Alex A. Archer')

    def test_admin_can_change_number(self):
        response = self._put(ADMIN, {'Number': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._stored('Number'), '1')


if __name__ == '__main__':
    unittest.main()
