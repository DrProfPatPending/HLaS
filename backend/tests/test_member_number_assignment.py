import unittest
from unittest import mock

from flask import Flask
from sqlalchemy import BigInteger, Column, Integer, MetaData, String, Table, create_engine, select, text
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.postgres_backend import _build_postgres_member_values
from routes.member_routes import create_member_blueprint


class _Deps(dict):
    def __missing__(self, key):
        return mock.Mock(name=key)


def _memory_engine():
    return create_engine(
        'sqlite+pysqlite://', future=True,
        connect_args={'check_same_thread': False}, poolclass=StaticPool,
    )


def _client(**overrides):
    deps = _Deps(
        require_permission=lambda permission, club=None: None,
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


class MemberNumberPostgresTests(unittest.TestCase):
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
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('club_id', BigInteger, nullable=False),
            Column('number', String(64), nullable=False, server_default=''),
            Column('members_name', String(255), nullable=False, server_default=''),
            Column('member_type', String(120), nullable=False, server_default=''),
            Column('paid_up_2026', String(32), nullable=False, server_default=''),
        )
        metadata.create_all(engine)
        self.session_factory = sessionmaker(bind=engine, future=True)
        with self.session_factory() as session:
            for club_id, number in ((1, '41'), (1, '9'), (1, 'H1'), (2, '500')):
                session.execute(self.members.insert().values(club_id=club_id, number=number, members_name='x'))
            session.commit()
        backend = {'session_factory': self.session_factory, 'members_table': self.members}
        self.client = _client(
            is_postgres_reads_enabled=lambda: True,
            is_postgres_writes_enabled=lambda: True,
            get_postgres_backend=lambda: backend,
        )

    def _numbers(self):
        with self.session_factory() as session:
            return session.execute(
                select(self.members.c.number).where(self.members.c.club_id == 1).order_by(self.members.c.id)
            ).scalars().all()

    def test_blank_number_gets_next_in_club(self):
        response = self.client.post('/members', json={'club': 'CTC', 'Members_Name': 'New Member'})
        self.assertEqual(response.status_code, 200)
        # Highest whole number in this club is 41; other clubs and non-numeric values are ignored.
        self.assertEqual(response.get_json()['number'], '42')
        self.assertEqual(self._numbers()[-1], '42')

        response = self.client.post('/members', json={'club': 'CTC', 'Members_Name': 'Another', 'Number': '  '})
        self.assertEqual(response.get_json()['number'], '43')

    def test_entered_number_is_kept(self):
        response = self.client.post('/members', json={'club': 'CTC', 'Members_Name': 'New', 'Number': '100'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._numbers()[-1], '100')
        # CORE-35: the account, link and member role are created straight away.
        self.seed_accounts.assert_called_once()
        self.assertEqual(self.sync_roles.call_count, 1)
        self.assertIsNotNone(self.sync_roles.call_args.kwargs['club_id'])

    def test_duplicate_number_is_rejected(self):
        response = self.client.post('/members', json={'club': 'CTC', 'Members_Name': 'New', 'Number': '41'})
        self.assertEqual(response.status_code, 409)
        self.assertIn('41', response.get_json()['error'])
        self.assertEqual(len(self._numbers()), 3)


class MemberNumberSqliteTests(unittest.TestCase):
    def setUp(self):
        engine = _memory_engine()
        self.addCleanup(engine.dispose)
        with engine.begin() as conn:
            conn.execute(text(
                'CREATE TABLE members (ID INTEGER PRIMARY KEY, Number TEXT, Members_Name TEXT, '
                'Member_Type TEXT, Paid_Up_2026 TEXT)'
            ))
            conn.execute(text("INSERT INTO members (Number, Members_Name) VALUES ('7', 'a'), ('12', 'b')"))
        metadata = MetaData()
        metadata.reflect(bind=engine)
        base = automap_base(metadata=metadata)
        base.prepare()
        self.session = sessionmaker(bind=engine, future=True)()
        self.addCleanup(self.session.close)
        db_info = {'session': self.session, 'members_table': metadata.tables['members'], 'Member': base.classes.members}
        get_column = lambda name, table: next(  # noqa: E731
            (column for column in table.columns if column.name.lower() == str(name).lower()), None)
        self.client = _client(get_db_for_club=lambda club: db_info, get_column=get_column)

    def test_blank_number_gets_next(self):
        response = self.client.post('/members', json={'club': 'CTC', 'Members_Name': 'New'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['number'], '13')
        stored = self.session.execute(text("SELECT Number FROM members WHERE Members_Name = 'New'")).scalar_one()
        self.assertEqual(stored, '13')

    def test_duplicate_number_is_rejected(self):
        response = self.client.post('/members', json={'club': 'CTC', 'Members_Name': 'New', 'Number': '7'})
        self.assertEqual(response.status_code, 409)


if __name__ == '__main__':
    unittest.main()
