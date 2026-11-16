import unittest

from flask import Flask
from sqlalchemy import JSON, Boolean, Column, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.orm import sessionmaker

from mini_site_pages import normalize_pages_config
from routes.mini_site_routes import create_mini_site_routes


class MiniSiteContentTests(unittest.TestCase):
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

    def test_page_copy_survives_save_and_reload(self):
        response = self.client.put('/mini-site', json={
            'club': 'CTC',
            'enabled': True,
            'pages': [
                {
                    'id': 'about',
                    'enabled': True,
                    'headline': 'Our Club',
                    'subheading': 'A short introduction',
                    'content': '<p>About content</p>',
                },
            ],
        })
        self.assertEqual(response.status_code, 200)

        loaded = self.client.get('/mini-site?club=CTC').get_json()
        pages = {page['id']: page for page in loaded['pages']}
        self.assertEqual(pages['about']['headline'], 'Our Club')
        self.assertEqual(pages['about']['subheading'], 'A short introduction')
        self.assertEqual(pages['about']['content'], '<p>About content</p>')

        with self.engine.connect() as conn:
            persisted = conn.execute(select(self.mini_sites.c.pages)).scalar_one()
        self.assertEqual(persisted, loaded['pages'])

    def test_page_copy_fields_can_be_cleared_to_restore_template(self):
        pages = normalize_pages_config([
            {
                'id': 'about',
                'headline': '',
                'subheading': '',
                'content': '',
            },
        ])
        about_page = next(page for page in pages if page['id'] == 'about')
        self.assertEqual(about_page.get('headline', ''), '')
        self.assertEqual(about_page.get('subheading', ''), '')
        self.assertEqual(about_page.get('content', ''), '')


if __name__ == '__main__':
    unittest.main()
