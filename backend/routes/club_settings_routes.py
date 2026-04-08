import json
import os

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, select


CLUB_SETTINGS_KEY = 'club_settings'
CATCH_RETURN_FIELD_KEYS = (
    'sessionDate',
    'beatId',
    'smallTrout',
    'mediumTrout',
    'largeTrout',
    'smallGrayling',
    'mediumGrayling',
    'largeGrayling',
    'otherFish',
    'fliesUsed',
    'weatherConditions',
    'predatorDamage',
)
DEFAULT_CATCH_RETURN_FIELD_VISIBILITY = {
    field_key: True for field_key in CATCH_RETURN_FIELD_KEYS
}


def _club_scope(club_short_name):
    return f"club:{str(club_short_name or '').strip()}"


def _club_settings_path(deps):
    app_data_dir = deps.get('APP_DATA_DIR') or os.path.dirname(__file__)
    return os.path.join(app_data_dir, 'club_settings.json')


def _normalize_field_visibility(raw_value):
    source = raw_value if isinstance(raw_value, dict) else {}
    normalized = {**DEFAULT_CATCH_RETURN_FIELD_VISIBILITY}
    for key in CATCH_RETURN_FIELD_KEYS:
        if key in source:
            normalized[key] = bool(source.get(key))
    return normalized


def _normalize_club_settings(raw_value):
    source = raw_value if isinstance(raw_value, dict) else {}
    return {
        'catchReturnFieldVisibility': _normalize_field_visibility(source.get('catchReturnFieldVisibility')),
    }


def _load_all_club_settings_from_json(deps):
    settings_path = _club_settings_path(deps)
    if not os.path.exists(settings_path):
        return {}
    try:
        with open(settings_path, 'r', encoding='utf-8') as file_handle:
            loaded = json.load(file_handle)
        return loaded if isinstance(loaded, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_all_club_settings_to_json(all_settings, deps):
    settings_path = _club_settings_path(deps)
    with open(settings_path, 'w', encoding='utf-8') as file_handle:
        json.dump(all_settings, file_handle, indent=2)
        file_handle.write('\n')


def load_club_settings_for_club(club_short_name, deps):
    normalized_club = str(club_short_name or '').strip()
    if not normalized_club:
        return _normalize_club_settings({})

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
                        and_(
                            app_settings_table.c.scope == _club_scope(normalized_club),
                            app_settings_table.c.key == CLUB_SETTINGS_KEY,
                        )
                    )
                ).first()
            finally:
                session.close()

            loaded = row[0] if row else None
            return _normalize_club_settings(loaded)
        except Exception:
            pass

    all_settings = _load_all_club_settings_from_json(deps)
    loaded = all_settings.get(normalized_club, {}) if isinstance(all_settings, dict) else {}
    return _normalize_club_settings(loaded)


def save_club_settings_for_club(club_short_name, settings, deps):
    normalized_club = str(club_short_name or '').strip()
    if not normalized_club:
        raise ValueError('Club is required')

    normalized_settings = _normalize_club_settings(settings)

    all_settings = _load_all_club_settings_from_json(deps)
    all_settings[normalized_club] = normalized_settings
    _save_all_club_settings_to_json(all_settings, deps)

    is_postgres_writes_enabled = deps.get('is_postgres_writes_enabled')
    get_postgres_backend = deps.get('get_postgres_backend')
    if callable(is_postgres_writes_enabled) and callable(get_postgres_backend) and is_postgres_writes_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        app_settings_table = backend['app_settings_table']
        try:
            existing = session.execute(
                select(app_settings_table.c.id).where(
                    and_(
                        app_settings_table.c.scope == _club_scope(normalized_club),
                        app_settings_table.c.key == CLUB_SETTINGS_KEY,
                    )
                )
            ).first()

            if existing:
                session.execute(
                    app_settings_table.update()
                    .where(app_settings_table.c.id == existing[0])
                    .values(value=normalized_settings)
                )
            else:
                session.execute(
                    app_settings_table.insert().values(
                        scope=_club_scope(normalized_club),
                        key=CLUB_SETTINGS_KEY,
                        value=normalized_settings,
                    )
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return normalized_settings


def create_club_settings_blueprint(deps):
    bp = Blueprint('club_settings', __name__)

    get_current_principal = deps['get_current_principal']
    require_authenticated = deps['require_authenticated']
    require_permission = deps['require_permission']

    @bp.route('/club-settings', methods=['GET'])
    def get_club_settings():
        requested_club = str(request.args.get('club', '')).strip()
        auth_error = require_authenticated(requested_club)
        if auth_error:
            return auth_error

        principal = get_current_principal(requested_club)
        if principal is None:
            return jsonify({'error': 'Unauthorized'}), 401

        club = str(principal.get('scope_club_short_name') or principal.get('club_short_name') or '').strip()
        if not club:
            return jsonify({'error': 'Club is required'}), 400

        settings = load_club_settings_for_club(club, deps)
        return jsonify({'club': club, 'settings': settings})

    @bp.route('/club-settings', methods=['POST', 'PUT'])
    def set_club_settings():
        payload = request.json or {}
        requested_club = str(payload.get('club') or request.args.get('club') or '').strip()
        auth_error = require_permission('member.club.list', requested_club)
        if auth_error:
            return auth_error

        principal = get_current_principal(requested_club)
        if principal is None:
            return jsonify({'error': 'Unauthorized'}), 401

        club = str(principal.get('scope_club_short_name') or principal.get('club_short_name') or '').strip()
        if not club:
            return jsonify({'error': 'Club is required'}), 400

        settings = payload.get('settings', payload)
        try:
            normalized = save_club_settings_for_club(club, settings, deps)
            return jsonify({'success': True, 'club': club, 'settings': normalized})
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    return bp
