import importlib
import os
import unittest
from unittest import mock


class StartupSyncTests(unittest.TestCase):
    def test_filesystem_sync_can_be_disabled_without_changing_default(self):
        with mock.patch(
            'db.postgres_backend.get_postgres_backend',
            return_value={'engine': mock.Mock()},
        ), mock.patch.dict(os.environ, {'ENABLE_BACKUPS': 'false'}):
            app_module = importlib.import_module('app')
            for value in (None, 'false'):
                with self.subTest(value=value), mock.patch.dict(os.environ):
                    if value is None:
                        os.environ.pop('HLAS_SYNC_FILES_ON_STARTUP', None)
                    else:
                        os.environ['HLAS_SYNC_FILES_ON_STARTUP'] = value
                    with mock.patch.object(app_module, '_register_beats_sync_startup') as beats, \
                            mock.patch.object(app_module, '_register_logos_sync_startup') as images:
                        app = app_module.create_app()
                    if value is None:
                        beats.assert_called_once_with(app)
                        images.assert_called_once_with(app)
                    else:
                        beats.assert_not_called()
                        images.assert_not_called()
