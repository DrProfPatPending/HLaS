import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from flask import Blueprint, jsonify, request, send_from_directory
from routes.field_order_routes import load_field_order_config


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

    @bp.route('/field-order', methods=['GET'])
    def get_field_order():
        try:
            return jsonify({'field_order': load_field_order_config(deps)})
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

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


    from sqlalchemy import select
    from db_models import club_logos
    from flask import Response, current_app

    @bp.route('/club_logo/<short_name>', methods=['GET'])
    def club_logo(short_name):
        import logging
        logger = logging.getLogger("club_logo")
        logger.debug(f"Request for club logo: {short_name}")
        db_engine = deps.get('db_engine')
        logger.debug(f"db_engine from deps: {db_engine}")
        if db_engine is None:
            db_engine = getattr(current_app, 'db_engine', None)
            logger.debug(f"db_engine from current_app: {db_engine}")
        if db_engine is None:
            logger.error("Database engine not available")
            return jsonify({'error': 'Database engine not available'}), 500
        try:
            with db_engine.connect() as conn:
                stmt = select(
                    club_logos.c.image_data,
                    club_logos.c.mime_type
                ).where(club_logos.c.club_short_name == short_name)
                logger.debug(f"SQL statement: {stmt}")
                result = conn.execute(stmt).first()
                logger.debug(f"Query result: {result}")
                if not result:
                    logger.warning(f"Logo not found for club: {short_name}")
                    return jsonify({'error': 'Logo not found'}), 404
                image_data, mime_type = result
                logger.debug(f"image_data type: {type(image_data)}, mime_type: {mime_type}")
                return Response(image_data, mimetype=mime_type)
        except Exception as e:
            logger.exception(f"Exception in club_logo endpoint for club {short_name}: {e}")
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    return bp
