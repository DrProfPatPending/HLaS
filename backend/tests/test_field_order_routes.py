import json
import os
import tempfile
import unittest

from sqlalchemy import JSON, Column, Integer, MetaData, String, Table, and_, create_engine, select
from sqlalchemy.orm import sessionmaker

from routes import field_order_routes


class FieldOrderRoutesPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.original_field_order_path = field_order_routes.FIELD_ORDER_PATH

        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_field_order_path = os.path.join(self.temp_dir.name, 'field_order.json')

        self.default_config = {
            'my_club': ['Members_Name', 'E_Mail'],
            'home_news': ['Date', 'Category', 'Update', 'Status'],
            'show_columns': {
                'home_news': {
                    'Date': True,
                    'Category': True,
                    'Update': True,
                    'Status': True,
                }
            },
            'display_names': {
                'home_news': {
                    'Update': 'Update',
                }
            },
            'minimum_widths': {
                'home_news': {
                    'Update': 260,
                }
            },
            'widths': {
                'home_news': {
                    'Update': 'flex',
                }
            },
            'read_only': {
                'my_club': {},
                'home_news': {},
            },
        }

        with open(self.temp_field_order_path, 'w', encoding='utf-8') as handle:
            json.dump(self.default_config, handle)

        field_order_routes.FIELD_ORDER_PATH = self.temp_field_order_path

        engine = create_engine('sqlite+pysqlite:///:memory:', future=True)
        metadata = MetaData()
        self.app_settings_table = Table(
            'app_settings',
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('scope', String(64), nullable=False),
            Column('key', String(128), nullable=False),
            Column('value', JSON, nullable=False),
        )
        metadata.create_all(engine)

        self.session_factory = sessionmaker(bind=engine, future=True)

    def tearDown(self):
        field_order_routes.FIELD_ORDER_PATH = self.original_field_order_path
        self.temp_dir.cleanup()

    def _deps(self, read_enabled=True, write_enabled=True):
        return {
            'is_postgres_reads_enabled': lambda: read_enabled,
            'is_postgres_writes_enabled': lambda: write_enabled,
            'get_postgres_backend': lambda: {
                'session_factory': self.session_factory,
                'app_settings_table': self.app_settings_table,
            },
        }

    def _fetch_stored_field_order(self):
        session = self.session_factory()
        try:
            row = session.execute(
                select(self.app_settings_table.c.value).where(
                    and_(
                        self.app_settings_table.c.scope == 'global',
                        self.app_settings_table.c.key == 'field_order',
                    )
                )
            ).first()
            return row[0] if row else None
        finally:
            session.close()

    def test_save_field_order_persists_all_configurable_properties_to_postgres(self):
        payload = {
            'my_club': ['Members_Name', 'E_Mail'],
            'home_news': ['Date', 'Category', 'Update', 'Status'],
            'show_columns': {
                'home_news': {
                    'Date': True,
                    'Category': False,
                    'Update': True,
                    'Status': True,
                }
            },
            'display_names': {
                'home_news': {
                    'Update': 'Headline',
                }
            },
            'minimum_widths': {
                'home_news': {
                    'Update': 320,
                }
            },
            'widths': {
                'home_news': {
                    'Update': '50%',
                }
            },
            'read_only': {
                'home_news': {
                    'Update': 1,
                    'Category': 0,
                }
            },
        }

        field_order_routes.save_field_order_config(payload, self._deps())

        stored = self._fetch_stored_field_order()
        self.assertIsInstance(stored, dict)
        self.assertIn('read_only', stored)

        self.assertEqual(stored['show_columns']['home_news']['Category'], False)
        self.assertEqual(stored['display_names']['home_news']['Update'], 'Headline')
        self.assertEqual(stored['minimum_widths']['home_news']['Update'], 320)
        self.assertEqual(stored['widths']['home_news']['Update'], '50%')
        self.assertEqual(stored['read_only']['home_news']['Update'], True)
        self.assertEqual(stored['read_only']['home_news']['Category'], False)

    def test_load_field_order_reads_postgres_and_keeps_all_property_maps(self):
        postgres_value = {
            'home_news': ['Date', 'Category', 'Update', 'Status'],
            'show_columns': {
                'home_news': {
                    'Date': True,
                    'Category': True,
                    'Update': False,
                    'Status': True,
                }
            },
            'display_names': {
                'home_news': {
                    'Update': 'Club Update',
                }
            },
            'minimum_widths': {
                'home_news': {
                    'Update': 280,
                }
            },
            'widths': {
                'home_news': {
                    'Update': 'flex',
                }
            },
            'read_only': {
                'home_news': {
                    'Update': 1,
                },
                'custom_context': {
                    'Some_Field': 'yes',
                },
            },
            'show_columns': {
                'home_news': {
                    'Date': True,
                    'Category': True,
                    'Update': False,
                    'Status': True,
                },
                'custom_context': {
                    'Some_Field': True,
                },
            },
        }

        session = self.session_factory()
        try:
            session.execute(
                self.app_settings_table.insert().values(
                    scope='global',
                    key='field_order',
                    value=postgres_value,
                )
            )
            session.commit()
        finally:
            session.close()

        loaded = field_order_routes.load_field_order_config(self._deps())

        self.assertEqual(loaded['display_names']['home_news']['Update'], 'Club Update')
        self.assertEqual(loaded['minimum_widths']['home_news']['Update'], 280)
        self.assertEqual(loaded['widths']['home_news']['Update'], 'flex')
        self.assertEqual(loaded['show_columns']['home_news']['Update'], False)
        self.assertEqual(loaded['read_only']['home_news']['Update'], True)
        self.assertEqual(loaded['read_only']['custom_context']['Some_Field'], True)


if __name__ == '__main__':
    unittest.main()
