"""Saving club settings is for club admins and above, not committee (CORE-41)."""
import unittest
from unittest import mock

from flask import Flask, jsonify

from routes.club_settings_routes import create_club_settings_blueprint
from security.permissions import has_permission


class ClubSettingsSavePermissionTests(unittest.TestCase):
    def _client(self, roles):
        def require_permission(permission, club=''):
            if not has_permission(set(roles), permission):
                return jsonify({'error': 'Forbidden'}), 403
            return None

        deps = {
            'get_current_principal': lambda club='': {'scope_club_short_name': 'CTC'},
            'require_authenticated': lambda club='': None,
            'require_permission': require_permission,
        }
        app = Flask(__name__)
        app.register_blueprint(create_club_settings_blueprint(deps))
        return app.test_client()

    def _put(self, roles):
        with mock.patch('routes.club_settings_routes.save_club_settings_for_club', return_value={}) as save:
            response = self._client(roles).put('/club-settings', json={'club': 'CTC', 'settings': {}})
        return response, save

    def test_committee_cannot_save(self):
        response, save = self._put({'member', 'committee'})
        self.assertEqual(response.status_code, 403)
        save.assert_not_called()

    def test_member_cannot_save(self):
        response, save = self._put({'member'})
        self.assertEqual(response.status_code, 403)
        save.assert_not_called()

    def test_club_admin_can_save(self):
        response, save = self._put({'member', 'club_admin'})
        self.assertEqual(response.status_code, 200)
        save.assert_called_once()


if __name__ == '__main__':
    unittest.main()
