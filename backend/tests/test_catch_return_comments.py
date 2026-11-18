import unittest
from unittest import mock

from flask import Flask
from sqlalchemy import (
    BigInteger, Column, Date, DateTime, Integer, MetaData, String, Table, Text,
    create_engine, func, select, text,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from routes.member_routes import create_member_blueprint


class _Deps(dict):
    """Route deps with harmless mocks for everything the catch-return routes don't use."""

    def __missing__(self, key):
        return mock.Mock(name=key)


def _memory_engine():
    return create_engine(
        'sqlite+pysqlite://', future=True,
        connect_args={'check_same_thread': False}, poolclass=StaticPool,
    )


def _make_client(**overrides):
    deps = _Deps(
        require_authenticated=lambda club=None: None,
        get_current_principal=lambda club=None: {'member_id': 7, 'club_short_name': 'CTC'},
        is_postgres_reads_enabled=lambda: False,
        is_postgres_writes_enabled=lambda: False,
        _resolve_postgres_club_id=lambda session, club: 1,
    )
    deps.update(overrides)
    app = Flask(__name__)
    app.register_blueprint(create_member_blueprint(deps))
    return app.test_client()


def _catch_return(**extra):
    payload = {'club': 'CTC', 'date': '2026-05-01', 'beat_id': 'A', 'small_trout': 1}
    payload.update(extra)
    return payload


class CatchReturnCommentsPostgresTests(unittest.TestCase):
    def setUp(self):
        engine = _memory_engine()
        self.addCleanup(engine.dispose)
        metadata = MetaData()
        self.table = Table(
            'catch_returns', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('club_id', BigInteger, nullable=False),
            Column('member_id', BigInteger, nullable=False),
            Column('session_date', Date, nullable=False),
            Column('beat_id', String(64), nullable=False, server_default=''),
            *[Column(name, Integer, nullable=False, server_default='0') for name in (
                'small_trout', 'medium_trout', 'large_trout',
                'small_grayling', 'medium_grayling', 'large_grayling', 'other_fish',
            )],
            *[Column(name, Text, nullable=False, server_default='') for name in (
                'flies_used', 'weather_conditions', 'predator_damage', 'comments',
            )],
            Column('created_at', DateTime, nullable=False, server_default=func.now()),
            Column('updated_at', DateTime, nullable=False, server_default=func.now()),
        )
        metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine, future=True)
        self.session_factory = session_factory
        backend = {'session_factory': session_factory, 'catch_returns_table': self.table}
        self.client = _make_client(
            is_postgres_reads_enabled=lambda: True,
            is_postgres_writes_enabled=lambda: True,
            get_postgres_backend=lambda: backend,
        )

    def _stored_comments(self):
        with self.session_factory() as session:
            return [row[0] for row in session.execute(select(self.table.c.comments).order_by(self.table.c.id))]

    def test_comments_are_saved_and_listed(self):
        response = self.client.post('/catch-returns', json=_catch_return(comments='  Rose to a sedge at dusk.  '))
        self.assertEqual(response.status_code, 201)

        listed = self.client.get('/catch-returns/mine?club=CTC').get_json()['returns']
        self.assertEqual(listed[0]['comments'], 'Rose to a sedge at dusk.')
        self.assertEqual(self._stored_comments(), ['Rose to a sedge at dusk.'])

    def test_comments_are_optional(self):
        response = self.client.post('/catch-returns', json=_catch_return())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self._stored_comments(), [''])

    def test_comments_over_limit_are_rejected(self):
        response = self.client.post('/catch-returns', json=_catch_return(comments='x' * 501))
        self.assertEqual(response.status_code, 400)
        self.assertIn('500 characters', response.get_json()['error'])
        self.assertEqual(self._stored_comments(), [])

        response = self.client.post('/catch-returns', json=_catch_return(comments='x' * 500))
        self.assertEqual(response.status_code, 201)


class CatchReturnCommentsSqliteFallbackTests(unittest.TestCase):
    def test_existing_table_without_comments_gains_the_column(self):
        engine = _memory_engine()
        self.addCleanup(engine.dispose)
        with engine.begin() as conn:
            conn.execute(text(
                """
                CREATE TABLE catch_returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER NOT NULL,
                    session_date TEXT NOT NULL,
                    beat_id TEXT NOT NULL DEFAULT '',
                    small_trout INTEGER NOT NULL DEFAULT 0,
                    medium_trout INTEGER NOT NULL DEFAULT 0,
                    large_trout INTEGER NOT NULL DEFAULT 0,
                    small_grayling INTEGER NOT NULL DEFAULT 0,
                    medium_grayling INTEGER NOT NULL DEFAULT 0,
                    large_grayling INTEGER NOT NULL DEFAULT 0,
                    other_fish INTEGER NOT NULL DEFAULT 0,
                    flies_used TEXT NOT NULL DEFAULT '',
                    weather_conditions TEXT NOT NULL DEFAULT '',
                    predator_damage TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            ))
            conn.execute(text("INSERT INTO catch_returns (member_id, session_date, beat_id) VALUES (7, '2026-04-01', 'B')"))

        session = sessionmaker(bind=engine, future=True)()
        db_info = {'session': session}
        client = _make_client(get_db_for_club=lambda club: db_info, get_read_db_for_club=lambda club: db_info)
        try:
            response = client.post('/catch-returns', json=_catch_return(comments='Water carrying colour.'))
            self.assertEqual(response.status_code, 201)

            listed = client.get('/catch-returns/mine?club=CTC').get_json()['returns']
            self.assertEqual([row['comments'] for row in listed], ['Water carrying colour.', ''])
        finally:
            session.close()


if __name__ == '__main__':
    unittest.main()
