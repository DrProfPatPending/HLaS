import unittest

from sqlalchemy import JSON, Boolean, Column, Integer, MetaData, String, Table, create_engine, select

from sync_beats_json_to_postgres import sync_club_beats


class SyncClubBeatsTests(unittest.TestCase):
    """Startup beats sync must seed empty clubs without overwriting app edits."""

    def setUp(self):
        self.engine = create_engine('sqlite+pysqlite:///:memory:', future=True)
        metadata = MetaData()
        self.clubs = Table(
            'clubs', metadata,
            Column('id', Integer, primary_key=True),
            Column('short_name', String(32), nullable=False),
            Column('is_active', Boolean, nullable=False),
        )
        text_columns = [
            'beat_name', 'beat_id', 'river', 'position', 'beat_upstream', 'beat_downstream',
            'beat_description', 'detailed_description', 'beat_upstream_latitude',
            'beat_upstream_longitude', 'beat_downstream_latitude', 'beat_downstream_longitude',
        ]
        self.club_beats = Table(
            'club_beats', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('club_id', Integer, nullable=False),
            *[Column(name, String) for name in text_columns],
            Column('parking_locations', JSON),
            Column('pools', JSON),
            Column('waypoints', JSON),
        )
        metadata.create_all(self.engine)

        with self.engine.begin() as conn:
            conn.execute(self.clubs.insert(), [
                {'id': 1, 'short_name': 'CTC', 'is_active': True},
                {'id': 2, 'short_name': 'NEW', 'is_active': True},
            ])
            conn.execute(self.club_beats.insert().values(
                club_id=1, beat_id='A', beat_name='Edited in app', parking_locations=[], pools=[], waypoints=[],
            ))

        self.json_beats = {
            'CTC': [{'Beat_ID': 'A', 'Beat_Name': 'From JSON'}, {'Beat_ID': 'B', 'Beat_Name': 'From JSON B'}],
            'NEW': [{'Beat_ID': 'N1', 'Beat_Name': 'Starter beat'}],
        }

    def _sync(self, **kwargs):
        with self.engine.begin() as conn:
            return sync_club_beats(conn, self.clubs, self.club_beats, self.json_beats, verbose=False, **kwargs)

    def _beat_names(self, club_id):
        with self.engine.connect() as conn:
            rows = conn.execute(
                select(self.club_beats.c.beat_name)
                .where(self.club_beats.c.club_id == club_id)
                .order_by(self.club_beats.c.beat_id)
            ).fetchall()
        return [row.beat_name for row in rows]

    def test_default_keeps_existing_beats_and_seeds_empty_club(self):
        written = self._sync()

        self.assertEqual(self._beat_names(1), ['Edited in app'])
        self.assertEqual(self._beat_names(2), ['Starter beat'])
        self.assertEqual(written, 1)

    def test_replace_existing_overwrites_from_json(self):
        written = self._sync(replace_existing=True)

        self.assertEqual(self._beat_names(1), ['From JSON', 'From JSON B'])
        self.assertEqual(self._beat_names(2), ['Starter beat'])
        self.assertEqual(written, 3)

    def test_dry_run_writes_nothing(self):
        self._sync(dry_run=True, replace_existing=True)

        self.assertEqual(self._beat_names(1), ['Edited in app'])
        self.assertEqual(self._beat_names(2), [])


if __name__ == '__main__':
    unittest.main()
