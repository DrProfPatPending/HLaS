import os
import json
from flask import Blueprint, jsonify, request
from sqlalchemy import and_, select

FIELD_ORDER_PATH = os.path.join(os.path.dirname(__file__), '../field_order.json')
FIELD_ORDER_KEY = 'field_order'


def _load_field_order_from_json():
    with open(FIELD_ORDER_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_field_order_to_json(data):
    with open(FIELD_ORDER_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def _merge_field_order_defaults(defaults, loaded):
    if not isinstance(defaults, dict):
        return loaded if isinstance(loaded, dict) else defaults

    merged = dict(defaults)
    if not isinstance(loaded, dict):
        return merged

    for key, loaded_value in loaded.items():
        default_value = defaults.get(key)
        if isinstance(default_value, dict) and isinstance(loaded_value, dict):
            merged[key] = _merge_field_order_defaults(default_value, loaded_value)
        else:
            merged[key] = loaded_value

    return merged


def _normalize_field_order_config(loaded, defaults=None):
    defaults = defaults if isinstance(defaults, dict) else {}
    merged = _merge_field_order_defaults(defaults, loaded if isinstance(loaded, dict) else {})

    read_only = merged.get('read_only')
    if not isinstance(read_only, dict):
        read_only = {}

    per_context_setting_keys = {
        'minimum_widths',
        'show_columns',
        'display_names',
        'read_only',
        'widths',
    }

    context_candidates = set()
    for key, value in merged.items():
        if key in per_context_setting_keys:
            continue
        if isinstance(value, list):
            context_candidates.add(key)

    for setting_key in per_context_setting_keys:
        setting_map = merged.get(setting_key)
        if isinstance(setting_map, dict):
            context_candidates.update(setting_map.keys())

    normalized_read_only = {}
    for context_key in context_candidates:
        raw_context = read_only.get(context_key)
        if not isinstance(raw_context, dict):
            normalized_read_only[context_key] = {}
            continue
        normalized_read_only[context_key] = {
            field_name: bool(is_read_only)
            for field_name, is_read_only in raw_context.items()
            if isinstance(field_name, str)
        }

    merged['read_only'] = normalized_read_only
    return merged


def _resolve_club_short_name(explicit_club, deps):
    requested_club = str(explicit_club or '').strip()
    get_current_principal = deps.get('get_current_principal')
    if not callable(get_current_principal):
        return requested_club

    principal = get_current_principal(requested_club)
    if not principal:
        return requested_club

    scoped = str(principal.get('scope_club_short_name') or '').strip()
    session_club = str(principal.get('club_short_name') or '').strip()
    return scoped or session_club or requested_club


def _load_field_order_from_postgres_for_club(club_short_name, deps):
    normalized_club = str(club_short_name or '').strip()
    if not normalized_club:
        return None

    is_postgres_reads_enabled = deps.get('is_postgres_reads_enabled')
    get_postgres_backend = deps.get('get_postgres_backend')
    if not (callable(is_postgres_reads_enabled) and callable(get_postgres_backend) and is_postgres_reads_enabled()):
        return None

    backend = get_postgres_backend()
    session = backend['session_factory']()
    club_field_order_table = backend.get('club_field_order_table')
    clubs_table = backend.get('clubs_table')
    if club_field_order_table is None or clubs_table is None:
        session.close()
        return None

    try:
        row = session.execute(
            select(club_field_order_table.c.config)
            .select_from(club_field_order_table.join(clubs_table, club_field_order_table.c.club_id == clubs_table.c.id))
            .where(
                and_(
                    clubs_table.c.short_name == normalized_club,
                    clubs_table.c.is_active.is_(True),
                )
            )
        ).first()
    finally:
        session.close()

    loaded = row[0] if row else None
    return loaded if isinstance(loaded, dict) else None


def _save_field_order_to_postgres_for_club(club_short_name, normalized_data, deps):
    normalized_club = str(club_short_name or '').strip()
    if not normalized_club:
        raise ValueError('Club is required')

    is_postgres_writes_enabled = deps.get('is_postgres_writes_enabled')
    get_postgres_backend = deps.get('get_postgres_backend')
    if not (callable(is_postgres_writes_enabled) and callable(get_postgres_backend) and is_postgres_writes_enabled()):
        raise RuntimeError('PostgreSQL writes are not enabled')

    backend = get_postgres_backend()
    session = backend['session_factory']()
    club_field_order_table = backend.get('club_field_order_table')
    clubs_table = backend.get('clubs_table')
    if club_field_order_table is None or clubs_table is None:
        session.close()
        raise RuntimeError('club_field_order table is unavailable')

    try:
        club_id = session.execute(
            select(clubs_table.c.id).where(
                and_(
                    clubs_table.c.short_name == normalized_club,
                    clubs_table.c.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if club_id is None:
            raise ValueError('Club not found')

        existing = session.execute(
            select(club_field_order_table.c.id).where(club_field_order_table.c.club_id == club_id)
        ).first()

        if existing:
            session.execute(
                club_field_order_table.update()
                .where(club_field_order_table.c.id == existing[0])
                .values(config=normalized_data)
            )
        else:
            session.execute(
                club_field_order_table.insert().values(club_id=club_id, config=normalized_data)
            )

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def load_field_order_config(deps=None, club_short_name=''):
    deps = deps or {}
    default_config = _normalize_field_order_config(_load_field_order_from_json())

    normalized_club = str(club_short_name or '').strip()
    if normalized_club:
        try:
            loaded = _load_field_order_from_postgres_for_club(normalized_club, deps)
            if isinstance(loaded, dict) and loaded:
                return _normalize_field_order_config(loaded, default_config)
        except Exception:
            pass

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
                        and_(app_settings_table.c.scope == 'global', app_settings_table.c.key == FIELD_ORDER_KEY)
                    )
                ).first()
            finally:
                session.close()

            loaded = row[0] if row else None
            if isinstance(loaded, dict) and loaded:
                return _normalize_field_order_config(loaded, default_config)
        except Exception:
            pass

    return default_config


def save_field_order_config(data, deps=None):
    deps = deps or {}
    default_config = _normalize_field_order_config(_load_field_order_from_json())
    normalized_data = _normalize_field_order_config(data, default_config)
    _save_field_order_to_json(normalized_data)

    is_postgres_writes_enabled = deps.get('is_postgres_writes_enabled')
    get_postgres_backend = deps.get('get_postgres_backend')

    if callable(is_postgres_writes_enabled) and callable(get_postgres_backend) and is_postgres_writes_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        app_settings_table = backend['app_settings_table']
        try:
            existing = session.execute(
                select(app_settings_table.c.id).where(
                    and_(app_settings_table.c.scope == 'global', app_settings_table.c.key == FIELD_ORDER_KEY)
                )
            ).first()

            if existing:
                session.execute(
                    app_settings_table.update()
                    .where(app_settings_table.c.id == existing[0])
                    .values(value=normalized_data)
                )
            else:
                session.execute(
                    app_settings_table.insert().values(scope='global', key=FIELD_ORDER_KEY, value=normalized_data)
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def create_field_order_blueprint(deps=None):
    deps = deps or {}
    bp = Blueprint('field_order', __name__)

    require_authenticated = deps.get('require_authenticated')
    require_permission = deps.get('require_permission')

    @bp.route('/admin/field-order', methods=['GET'])
    def get_field_order():
        requested_club = str(request.args.get('club', '')).strip()
        if callable(require_permission):
            auth_error = require_permission('system.settings', requested_club)
            if auth_error:
                return auth_error
        try:
            resolved_club = _resolve_club_short_name(requested_club, deps)
            data = load_field_order_config(deps, resolved_club)
            return jsonify({'field_order': data, 'club': resolved_club})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/admin/field-order', methods=['POST', 'PUT'])
    def set_field_order():
        requested_club = str(request.args.get('club', '')).strip()
        if callable(require_permission):
            auth_error = require_permission('system.settings', requested_club)
            if auth_error:
                return auth_error
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            requested_club = str(requested_club or data.get('club') or '').strip()
            if requested_club:
                normalized_data = _normalize_field_order_config(data.get('field_order', data), _normalize_field_order_config(_load_field_order_from_json()))
                _save_field_order_to_postgres_for_club(requested_club, normalized_data, deps)
                return jsonify({'success': True, 'club': requested_club})
            save_field_order_config(data, deps)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/club-field-order', methods=['GET'])
    def get_club_field_order():
        requested_club = str(request.args.get('club', '')).strip()
        if callable(require_permission):
            auth_error = require_permission('field_order.club.manage', requested_club)
            if auth_error:
                return auth_error
        elif callable(require_authenticated):
            auth_error = require_authenticated(requested_club)
            if auth_error:
                return auth_error

        try:
            resolved_club = _resolve_club_short_name(requested_club, deps)
            if not resolved_club:
                return jsonify({'error': 'Club is required'}), 400
            data = load_field_order_config(deps, resolved_club)
            return jsonify({'club': resolved_club, 'field_order': data})
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    @bp.route('/club-field-order', methods=['POST', 'PUT'])
    def set_club_field_order():
        payload = request.json or {}
        requested_club = str(payload.get('club') or request.args.get('club') or '').strip()
        if callable(require_permission):
            auth_error = require_permission('field_order.club.manage', requested_club)
            if auth_error:
                return auth_error

        try:
            resolved_club = _resolve_club_short_name(requested_club, deps)
            if not resolved_club:
                return jsonify({'error': 'Club is required'}), 400

            incoming = payload.get('field_order', payload)
            default_config = _normalize_field_order_config(_load_field_order_from_json())
            normalized_data = _normalize_field_order_config(incoming, default_config)
            _save_field_order_to_postgres_for_club(resolved_club, normalized_data, deps)
            return jsonify({'success': True, 'club': resolved_club, 'field_order': normalized_data})
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    return bp
