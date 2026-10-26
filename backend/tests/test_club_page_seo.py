import unittest
from unittest import mock

from flask import Flask
from sqlalchemy import JSON, Boolean, Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from routes.public_routes import create_public_blueprint

SHELL = '<html><head>\n  <title>HLaS Member login</title>\n</head><body></body></html>'
HEADERS = {'X-Forwarded-Proto': 'https', 'X-Forwarded-Host': 'example.org'}


class ClubPageSeoTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite://')
        metadata = MetaData()
        clubs = Table(
            'clubs', metadata,
            Column('id', Integer, primary_key=True),
            Column('short_name', String),
            Column('is_active', Boolean),
        )
        mini_sites = Table(
            'club_mini_sites', metadata,
            Column('id', Integer, primary_key=True),
            Column('club_id', Integer),
            Column('enabled', Boolean),
            Column('title', String),
            Column('tagline', String),
            Column('description', String),
            Column('hero_image_url', String),
            Column('pages', JSON),
        )
        metadata.create_all(engine)
        session_factory = sessionmaker(engine)
        with engine.begin() as conn:
            conn.execute(clubs.insert(), [
                {'id': 1, 'short_name': 'CTC', 'is_active': True},
                {'id': 2, 'short_name': 'OFF', 'is_active': True},
            ])
            conn.execute(mini_sites.insert(), [
                {
                    'club_id': 1, 'enabled': True, 'title': 'Cambridge "Trout" Club', 'tagline': '',
                    'description': 'We are <dedicated> to wild trout. ' * 10,
                    'hero_image_url': '/api/club_hero/CTC',
                    'pages': [{'id': 'about', 'enabled': True}, {'id': 'news', 'enabled': False}],
                },
                {
                    'club_id': 2, 'enabled': False, 'title': 'Off', 'tagline': '', 'description': '',
                    'hero_image_url': '', 'pages': [],
                },
            ])

        deps = {
            key: mock.MagicMock()
            for key in [
                'load_clubs_config', 'normalize_what3words_words', 'get_valid_club_short_names',
                'APP_DATA_DIR', 'get_read_db_for_club', 'get_column', 'get_club_logo_path', 'CLUB_LOGOS_DIR',
            ]
        }
        deps['get_postgres_backend'] = lambda: {
            'session_factory': session_factory,
            'clubs_table': clubs,
            'club_mini_sites_table': mini_sites,
        }
        deps['is_postgres_reads_enabled'] = lambda: True
        app = Flask(__name__)
        app.register_blueprint(create_public_blueprint(deps))
        self.client = app.test_client()

        patcher = mock.patch('routes.public_routes.urlopen')
        self.urlopen = patcher.start()
        self.urlopen.return_value.__enter__.return_value.read.return_value = SHELL.encode()
        self.addCleanup(patcher.stop)

    def get(self, path):
        response = self.client.get(path, headers=HEADERS)
        return response, response.get_data(as_text=True)

    def test_home_page_gets_title_description_canonical_and_og_tags(self):
        response, body = self.get('/club-page/CTC/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<title>Cambridge &quot;Trout&quot; Club</title>', body)
        self.assertNotIn('HLaS Member login', body)
        self.assertIn('<link rel="canonical" href="https://example.org/club/CTC/">', body)
        self.assertIn('name="description"', body)
        self.assertIn('&lt;dedicated&gt;', body)
        self.assertIn('property="og:image" content="https://example.org/api/club_hero/CTC"', body)
        self.assertNotIn('noindex', body)

    def test_description_is_truncated(self):
        _, body = self.get('/club-page/CTC/')
        start = body.index('name="description" content="') + len('name="description" content="')
        self.assertLessEqual(len(body[start:body.index('"', start)]), 200)

    def test_enabled_subpage_is_self_canonical_and_case_insensitive(self):
        _, body = self.get('/club-page/ctc/about')
        self.assertIn('href="https://example.org/club/CTC/about/"', body)

    def test_disabled_subpage_canonicalises_to_home(self):
        _, body = self.get('/club-page/CTC/news')
        self.assertIn('href="https://example.org/club/CTC/"', body)

    def test_login_page_is_noindex(self):
        response, body = self.get('/club-page/CTC/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('noindex', body)
        self.assertNotIn('rel="canonical"', body)

    def test_club_without_enabled_mini_site_is_noindex(self):
        response, body = self.get('/club-page/OFF/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('noindex', body)

    def test_unknown_club_is_404_noindex(self):
        response, body = self.get('/club-page/NOPE/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('noindex', body)

    def test_frontend_unavailable_returns_503(self):
        self.urlopen.side_effect = OSError('down')
        response, _ = self.get('/club-page/CTC/')
        self.assertEqual(response.status_code, 503)


if __name__ == '__main__':
    unittest.main()
