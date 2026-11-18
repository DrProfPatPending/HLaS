import base64
import json
import os
import tempfile
import unittest

from sqlalchemy import create_engine, text

import sync_documents_json_to_postgres as importer
import sync_documents_postgres_to_json as exporter

SCHEMA = [
    'CREATE TABLE clubs (id INTEGER PRIMARY KEY, short_name TEXT NOT NULL, full_name TEXT, description TEXT, '
    'website_url TEXT, admin_email TEXT, logo_url TEXT, whatsapp_groups TEXT, social_media TEXT, officers TEXT, '
    'is_active BOOLEAN NOT NULL, created_at TIMESTAMP, updated_at TIMESTAMP)',
    'CREATE TABLE app_users (id INTEGER PRIMARY KEY, username TEXT)',
    """CREATE TABLE club_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        club_id INTEGER NOT NULL,
        content_scope TEXT NOT NULL DEFAULT 'home',
        display_order INTEGER NOT NULL DEFAULT 0,
        title TEXT NOT NULL DEFAULT '',
        file_name TEXT NOT NULL DEFAULT '',
        file_ext TEXT NOT NULL DEFAULT '',
        mime_type TEXT NOT NULL DEFAULT '',
        file_size INTEGER NOT NULL DEFAULT 0,
        file_data BLOB NOT NULL,
        uploaded_by_user_id INTEGER,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
]


def _doc(scope, order, title, uploader, created='2026-11-18T10:00:00+00:00'):
    content = f'{scope}-{title}'.encode()
    return {
        'contentScope': scope, 'displayOrder': order, 'title': title, 'fileName': f'{title}.pdf',
        'fileExt': 'pdf', 'fileSize': len(content), 'mimeType': 'application/pdf',
        'uploadedBy': uploader, 'createdAt': created, 'fileContent': base64.b64encode(content).decode(),
    }


class DocumentsJsonRoundTripTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_url = f"sqlite:///{os.path.join(self.temp_dir.name, 'docs.db')}"
        engine = create_engine(self.db_url)
        self.addCleanup(engine.dispose)
        with engine.begin() as conn:
            for statement in SCHEMA:
                conn.execute(text(statement))
            conn.execute(text("INSERT INTO clubs (id, short_name, is_active) VALUES (1, 'CTC', 1)"))
            conn.execute(text("INSERT INTO app_users VALUES (224, 'admin')"))
        self.engine = engine
        os.environ['DATABASE_URL'] = self.db_url
        self.addCleanup(os.environ.pop, 'DATABASE_URL', None)

    def _write(self, name, docs):
        path = os.path.join(self.temp_dir.name, name)
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, 'documents.json'), 'w', encoding='utf-8') as handle:
            json.dump({'CTC': docs}, handle)
        return path

    def _rows(self):
        with self.engine.connect() as conn:
            return conn.execute(text(
                'SELECT content_scope, display_order, title, uploaded_by_user_id FROM club_documents '
                "ORDER BY CASE content_scope WHEN 'home' THEN 0 ELSE 1 END, content_scope, display_order"
            )).fetchall()

    def test_import_keeps_order_and_handles_unknown_uploaders(self):
        folder = self._write('in', [
            _doc('home', 2, 'Rules', 224),
            _doc('health-safety', 1, 'Risk Assessment', 999),  # uploader not in this database
            _doc('home', 1, 'Constitution', 224, created=''),
        ])
        # -f accepts the file itself as well as its folder.
        self.assertTrue(importer.sync_documents_to_postgres(os.path.join(folder, 'documents.json'), verbose=False))
        self.assertEqual(
            [tuple(row) for row in self._rows()],
            [('home', 1, 'Constitution', 224), ('home', 2, 'Rules', 224), ('health-safety', 1, 'Risk Assessment', None)],
        )

    def test_export_writes_display_order_in_app_order(self):
        folder = self._write('in', [
            _doc('health-safety', 1, 'Risk Assessment', 224),
            _doc('home', 2, 'Rules', 224, created='2026-11-18T12:00:00+00:00'),
            _doc('home', 1, 'Constitution', 224, created='2026-01-01T00:00:00+00:00'),
        ])
        self.assertTrue(importer.sync_documents_to_postgres(folder, verbose=False))

        exported = exporter.load_documents_from_postgres(self.db_url)['CTC']
        self.assertEqual(
            [(doc['contentScope'], doc['displayOrder'], doc['title']) for doc in exported],
            [('home', 1, 'Constitution'), ('home', 2, 'Rules'), ('health-safety', 1, 'Risk Assessment')],
        )

        # Exporting then importing keeps the order.
        self.assertTrue(importer.sync_documents_to_postgres(self._write('round-trip', exported), verbose=False))
        self.assertEqual([row[2] for row in self._rows()], ['Constitution', 'Rules', 'Risk Assessment'])


if __name__ == '__main__':
    unittest.main()
