import unittest
from unittest import mock

from flask import Flask, jsonify

from routes.public_routes import create_public_blueprint

CLUB = {
    'shortName': 'CTC',
    'fullName': 'Cambridge Trout Club',
    'description': 'A club',
    'websiteUrl': 'https://example.org/',
    'adminEmail': 'committee@example.org',
    'logoUrl': '/club_logo/CTC',
    'cssVariables': {'--app-color-link': '#5b3f9e'},
    'officers': [{'name': 'A Person', 'role': 'Treasurer', 'mobile': '07000 000000'}],
    'whatsappGroups': 'https://chat.whatsapp.com/secret-invite',
    'socialMedia': [{'platform': 'WhatsApp', 'url': 'https://chat.whatsapp.com/secret-invite'}],
    'beats': [{'Beat_ID': 'A', 'Beat_Upstream_Latitude': '52.07322'}],
    'smtp': {'host': 'smtp.example.org', 'username': 'user', 'password': 'secret-key'},
}

PRIVATE_MARKERS = ('secret-key', 'secret-invite', '07000 000000', '52.07322')


class PublicClubsRouteTests(unittest.TestCase):
    def _client(self, clubs, auth_result=None):
        deps = {
            key: mock.MagicMock()
            for key in [
                'normalize_what3words_words', 'get_valid_club_short_names', 'APP_DATA_DIR',
                'get_read_db_for_club', 'get_column', 'get_postgres_backend', 'get_club_logo_path',
                'CLUB_LOGOS_DIR',
            ]
        }
        deps['load_clubs_config'] = lambda: clubs
        deps['is_postgres_reads_enabled'] = lambda: True
        self.auth_calls = []

        def require_authenticated(club_short_name=''):
            self.auth_calls.append(club_short_name)
            return auth_result() if callable(auth_result) else auth_result

        deps['require_authenticated'] = require_authenticated
        app = Flask(__name__)
        app.register_blueprint(create_public_blueprint(deps))
        return app.test_client()

    def test_public_clubs_returns_only_allow_listed_fields(self):
        response = self._client([dict(CLUB)]).get('/clubs')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['clubs'], [{
            'shortName': 'CTC',
            'fullName': 'Cambridge Trout Club',
            'description': 'A club',
            'websiteUrl': 'https://example.org/',
            'adminEmail': 'committee@example.org',
            'logoUrl': '/club_logo/CTC',
            'cssVariables': {'--app-color-link': '#5b3f9e'},
        }])
        body = response.get_data(as_text=True)
        for marker in PRIVATE_MARKERS:
            self.assertNotIn(marker, body)

    def test_public_clubs_does_not_mutate_source_config(self):
        clubs = [dict(CLUB)]
        self._client(clubs).get('/clubs')
        self.assertIn('smtp', clubs[0])
        self.assertIn('officers', clubs[0])

    def test_public_clubs_handles_empty_config(self):
        response = self._client(None).get('/clubs')
        self.assertEqual(response.get_json(), {'clubs': []})

    def test_details_requires_authentication_for_that_club(self):
        client = self._client([dict(CLUB)], auth_result=lambda: (jsonify({'error': 'Unauthorized'}), 401))
        response = client.get('/clubs/CTC/details')

        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.auth_calls, ['CTC'])
        body = response.get_data(as_text=True)
        for marker in PRIVATE_MARKERS:
            self.assertNotIn(marker, body)

    def test_details_returns_member_fields_but_never_smtp(self):
        response = self._client([dict(CLUB)]).get('/clubs/CTC/details')

        self.assertEqual(response.status_code, 200)
        club = response.get_json()['club']
        self.assertNotIn('smtp', club)
        self.assertEqual(club['officers'], CLUB['officers'])
        self.assertEqual(club['whatsappGroups'], CLUB['whatsappGroups'])
        self.assertEqual(club['beats'], CLUB['beats'])
        self.assertNotIn('secret-key', response.get_data(as_text=True))
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_details_unknown_club(self):
        response = self._client([dict(CLUB)]).get('/clubs/NOPE/details')
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
