import unittest

from flask import Flask
from sqlalchemy import JSON, Boolean, Column, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.orm import sessionmaker

from mini_site_pages import normalize_pages_config
from routes.mini_site_routes import create_mini_site_routes


class MiniSiteHeroTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite://')
        metadata = MetaData()
        clubs = Table(
            'clubs', metadata,
            Column('id', Integer, primary_key=True),
            Column('short_name', String),
            Column('is_active', Boolean),
        )
        self.mini_sites = Table(
            'club_mini_sites', metadata,
            Column('id', Integer, primary_key=True),
            Column('club_id', Integer),
            Column('enabled', Boolean),
            Column('title', String),
            Column('tagline', String),
            Column('description', String),
            Column('hero_image_url', String),
            Column('pages', JSON),
            Column('social_links', JSON),
        )
        metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(clubs.insert(), {'id': 1, 'short_name': 'CTC', 'is_active': True})
        self.engine = engine
        self.addCleanup(engine.dispose)
        backend = {
            'session_factory': sessionmaker(engine),
            'clubs_table': clubs,
            'club_mini_sites_table': self.mini_sites,
        }
        deps = {
            'get_current_principal': lambda club: {'club_short_name': 'CTC'},
            'get_postgres_backend': lambda: backend,
            'is_postgres_reads_enabled': lambda: True,
            'is_postgres_writes_enabled': lambda: True,
            'require_authenticated': lambda club: None,
            'require_permission': lambda permission, club: None,
        }
        app = Flask(__name__)
        app.register_blueprint(create_mini_site_routes(deps))
        self.client = app.test_client()

    def test_page_image_and_fallback_survive_save_and_reload(self):
        response = self.client.put('/mini-site', json={
            'club': 'CTC',
            'enabled': True,
            'hero_image_url': '/api/club_hero/CTC',
            'pages': [
                {'id': 'about', 'enabled': True, 'content': 'About content',
                 'hero_image_url': ' /images/about.jpg ', 'hero_fallback': 'banner'},
                {'id': 'contact', 'enabled': True, 'hero_fallback': 'home'},
            ],
        })
        self.assertEqual(response.status_code, 200)
        loaded = self.client.get('/mini-site?club=CTC').get_json()
        pages = {page['id']: page for page in loaded['pages']}
        self.assertEqual(loaded['hero_image_url'], '/api/club_hero/CTC')
        self.assertEqual(pages['about']['hero_image_url'], '/images/about.jpg')
        self.assertEqual(pages['about']['hero_fallback'], 'banner')
        self.assertEqual(pages['about']['content'], 'About content')
        self.assertEqual(pages['contact']['hero_fallback'], 'home')
        with self.engine.connect() as conn:
            persisted = conn.execute(select(self.mini_sites.c.pages)).scalar_one()
        self.assertEqual(persisted, loaded['pages'])

    def test_existing_pages_default_to_home_image_fallback(self):
        pages = normalize_pages_config([{'id': 'about', 'enabled': True}])
        for page in pages:
            if page['id'] != 'home':
                self.assertEqual(page['hero_image_url'], '')
                self.assertEqual(page['hero_fallback'], 'home')

    def test_invalid_hero_settings_are_rejected_without_saving(self):
        for settings in [
            {'hero_image_url': 123},
            {'hero_image_url': 'javascript:alert(1)'},
            {'hero_image_url': '//example.org/image.jpg'},
            {'hero_fallback': 'invalid'},
        ]:
            with self.subTest(settings=settings):
                response = self.client.put('/mini-site', json={
                    'club': 'CTC', 'pages': [{'id': 'about', **settings}],
                })
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.get_json())
        with self.engine.connect() as conn:
            self.assertIsNone(conn.execute(select(self.mini_sites.c.id)).first())
