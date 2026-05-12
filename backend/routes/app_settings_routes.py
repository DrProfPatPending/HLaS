import json
import os

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, select

APP_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), '../app_settings.json')
APP_SETTINGS_KEY = 'app_settings'
DEFAULT_APP_SETTINGS = {
    'dateFormat': 'DD/MM/YY',
    'defaultClub': None,
}
ALLOWED_DATE_FORMATS = [
    'DD/MM/YY',
    'DD/MM/YYYY',
    'DD-MMM-YYYY',
    'YYYY-MM-DD',
    'MMM DD, YYYY',
    'DD MMM YYYY',
    'MM/DD/YYYY',
]


def _ensure_json_file_exists():
    if os.path.exists(APP_SETTINGS_PATH):
        return
    with open(APP_SETTINGS_PATH, 'w', encoding='utf-8') as file_handle:
        json.dump(DEFAULT_APP_SETTINGS, file_handle, indent=2)
        file_handle.write('\n')


def _load_app_settings_from_json():
    _ensure_json_file_exists()
    with open(APP_SETTINGS_PATH, 'r', encoding='utf-8') as file_handle:
        loaded = json.load(file_handle)
    if not isinstance(loaded, dict):
        return {**DEFAULT_APP_SETTINGS}
    return {
        **DEFAULT_APP_SETTINGS,
        **loaded,
    }


def _save_app_settings_to_json(data):
    with open(APP_SETTINGS_PATH, 'w', encoding='utf-8') as file_handle:
        json.dump(data, file_handle, indent=2)
        file_handle.write('\n')


def _normalize_app_settings(data):
    raw = data if isinstance(data, dict) else {}
    date_format = str(raw.get('dateFormat', DEFAULT_APP_SETTINGS['dateFormat'])).strip()
    if not date_format:
        date_format = DEFAULT_APP_SETTINGS['dateFormat']
    
    default_club = raw.get('defaultClub')
    if default_club is not None:
        default_club = str(default_club).strip() or None
    
    return {
        'dateFormat': date_format,
        'defaultClub': default_club,
    }


def load_app_settings_config(deps=None):
    deps = deps or {}
    is_postgres_reads_enabled = deps.get('is_postgres_reads_enabled')
    get_postgres_backend = deps.get('get_postgres_backend')

    if callable(is_postgres_reads_enabled) and callable(get_postgres_backend) and is_postgres_reads_enabled():
        try:
            backend = get_postgres_backend()
            session = backend['session_factory']()
            app_settings_table = backend['app_settings_table']
            try:
                row = session.execute(
                    select(app_settings_table.c.value).where(
                        and_(app_settings_table.c.scope == 'global', app_settings_table.c.key == APP_SETTINGS_KEY)
                    )
                ).first()
            finally:
                session.close()

            loaded = row[0] if row else None
            if isinstance(loaded, dict):
                return _normalize_app_settings(loaded)
        except Exception:
            pass

    return _load_app_settings_from_json()


def save_app_settings_config(data, deps=None):
    deps = deps or {}
    normalized = _normalize_app_settings(data)
    _save_app_settings_to_json(normalized)

    is_postgres_writes_enabled = deps.get('is_postgres_writes_enabled')
    get_postgres_backend = deps.get('get_postgres_backend')

    if callable(is_postgres_writes_enabled) and callable(get_postgres_backend) and is_postgres_writes_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        app_settings_table = backend['app_settings_table']
        try:
            existing = session.execute(
                select(app_settings_table.c.id).where(
                    and_(app_settings_table.c.scope == 'global', app_settings_table.c.key == APP_SETTINGS_KEY)
                )
            ).first()

            if existing:
                session.execute(
                    app_settings_table.update()
                    .where(app_settings_table.c.id == existing[0])
                    .values(value=normalized)
                )
            else:
                session.execute(
                    app_settings_table.insert().values(scope='global', key=APP_SETTINGS_KEY, value=normalized)
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def create_app_settings_blueprint(deps=None):
    deps = deps or {}
    bp = Blueprint('app_settings', __name__)

    def require_admin():
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or 'Bearer' not in auth_header:
            return jsonify({'error': 'Admin authentication required'}), 401
        return None

    def get_available_clubs():
        """Get list of available clubs sorted alphabetically."""
        try:
            load_clubs_config_func = deps.get('load_clubs_config')
            if callable(load_clubs_config_func):
                clubs = load_clubs_config_func()
                if isinstance(clubs, list):
                    # Sort clubs alphabetically by shortName
                    sorted_clubs = sorted(clubs, key=lambda c: str(c.get('shortName', '')).upper())
                    return [club.get('shortName') for club in sorted_clubs if club.get('shortName')]
        except Exception:
            pass
        return []

    @bp.route('/admin/app-settings', methods=['GET'])
    def get_app_settings():
        auth_error = require_admin()
        if auth_error:
            return auth_error
        try:
            settings = load_app_settings_config(deps)
            available_clubs = get_available_clubs()
            return jsonify({
                'settings': settings,
                'allowedDateFormats': ALLOWED_DATE_FORMATS,
                'availableClubs': available_clubs,
            })
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    @bp.route('/admin/app-settings', methods=['POST', 'PUT'])
    def set_app_settings():
        auth_error = require_admin()
        if auth_error:
            return auth_error

        payload = request.json or {}
        settings = payload.get('settings', payload)
        normalized = _normalize_app_settings(settings)

        if normalized['dateFormat'] not in ALLOWED_DATE_FORMATS:
            return jsonify({'error': 'Invalid date format option'}), 400

        # Validate defaultClub if not None or empty
        if normalized['defaultClub']:
            available_clubs = get_available_clubs()
            if normalized['defaultClub'] not in available_clubs:
                return jsonify({'error': f"Invalid default club: {normalized['defaultClub']}. Must be one of: {', '.join(available_clubs)}"}), 400

        try:
            save_app_settings_config(normalized, deps)
            return jsonify({'success': True, 'settings': normalized})
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    return bp
