import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from flask import Blueprint, jsonify, request, send_from_directory


def create_public_blueprint(deps):
    bp = Blueprint('public', __name__)

    load_clubs_config = deps['load_clubs_config']
    normalize_what3words_words = deps['normalize_what3words_words']
    get_valid_club_short_names = deps['get_valid_club_short_names']
    APP_DATA_DIR = deps['APP_DATA_DIR']
    get_club_logo_path = deps['get_club_logo_path']
    CLUB_LOGOS_DIR = deps['CLUB_LOGOS_DIR']

    @bp.route('/clubs', methods=['GET'])
    def get_clubs():
        return jsonify({'clubs': load_clubs_config()})

    @bp.route('/w3w/coordinates', methods=['GET'])
    def w3w_coordinates():
        words_param = request.args.get('words', '')
        words = normalize_what3words_words(words_param)
        if not words:
            return jsonify({'error': 'Invalid what3words address'}), 400

        api_key = os.getenv('WHAT3WORDS_API_KEY', '').strip()
        if not api_key:
            return jsonify({'error': 'WHAT3WORDS_API_KEY is not configured'}), 503

        lookup_url = (
            'https://api.what3words.com/v3/convert-to-coordinates'
            f'?words={quote(words)}&key={quote(api_key)}'
        )

        try:
            with urlopen(lookup_url, timeout=8) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode('utf-8'))
            except Exception:
                payload = {'error': str(exc)}
            return jsonify({'error': payload.get('error', 'Failed to resolve what3words')}), 502
        except URLError:
            return jsonify({'error': 'Unable to reach what3words service'}), 502
        except Exception:
            return jsonify({'error': 'Failed to resolve what3words'}), 502

        coordinates = payload.get('coordinates', {}) if isinstance(payload, dict) else {}
        lat = coordinates.get('lat')
        lng = coordinates.get('lng')
        if lat is None or lng is None:
            return jsonify({'error': 'No coordinates returned for what3words'}), 404

        return jsonify({'words': words, 'lat': lat, 'lng': lng})

    @bp.route('/member_photo/<club>/<path:filename>', methods=['GET'])
    def member_photo(club, filename):
        valid_clubs = get_valid_club_short_names()
        if club not in valid_clubs:
            return jsonify({'error': 'Invalid club'}), 404
        photo_dir = os.path.join(APP_DATA_DIR, 'ID_photos', club)
        if not os.path.isdir(photo_dir):
            return jsonify({'error': 'Photo directory not found'}), 404
        return send_from_directory(photo_dir, filename)

    @bp.route('/club_logo/<short_name>', methods=['GET'])
    def club_logo(short_name):
        logo_path = get_club_logo_path(short_name)
        if not os.path.exists(logo_path):
            return jsonify({'error': 'Logo not found'}), 404
        return send_from_directory(CLUB_LOGOS_DIR, os.path.basename(logo_path))

    return bp
