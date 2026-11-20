"""The app logger runs at INFO under gunicorn, and request logs redact query values."""
import importlib
import json
import logging
import os
import unittest
from unittest import mock


class RequestLoggingTests(unittest.TestCase):
    def setUp(self):
        patches = [
            mock.patch('db.postgres_backend.get_postgres_backend', return_value={'engine': mock.Mock()}),
            mock.patch.dict(os.environ, {'ENABLE_BACKUPS': 'false', 'HLAS_SYNC_FILES_ON_STARTUP': 'false'}),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        app_module = importlib.import_module('app')
        self.app = app_module.create_app()
        self.app.add_url_rule('/request-logging-test', view_func=lambda: 'ok')
        self.client = self.app.test_client()

    def test_app_logger_level_is_configured(self):
        # Under gunicorn nothing else sets it; it must not stay at WARNING.
        self.assertLessEqual(self.app.logger.getEffectiveLevel(), logging.INFO)

    def test_query_values_are_redacted_except_safe_keys(self):
        with self.assertLogs(self.app.logger, level='INFO') as logs:
            self.client.get('/request-logging-test?club=CTC&limit=50&Members_Name=*smith*&E_Mail=*@example.org')
        events = [json.loads(r.getMessage()) for r in logs.records if r.getMessage().startswith('{')]
        request_event = next(e for e in events if e.get('event') == 'http.request')
        self.assertEqual(request_event['query'],
                         {'club': 'CTC', 'limit': '50', 'Members_Name': '***', 'E_Mail': '***'})
        output = '\n'.join(r.getMessage() for r in logs.records)
        self.assertNotIn('smith', output)
        self.assertNotIn('example.org', output)


if __name__ == '__main__':
    unittest.main()
