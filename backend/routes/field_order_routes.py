import os
import json
from flask import Blueprint, jsonify, request
from sqlalchemy import and_, select

FIELD_ORDER_PATH = os.path.join(os.path.dirname(__file__), '../field_order.json')


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


def load_field_order_config(deps=None):
    deps = deps or {}
    default_config = _load_field_order_from_json()
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
                        and_(app_settings_table.c.scope == 'global', app_settings_table.c.key == 'field_order')
                    )
                ).first()
            finally:
                session.close()

            loaded = row[0] if row else None
            if isinstance(loaded, dict) and loaded:
                return _merge_field_order_defaults(default_config, loaded)
        except Exception:
            pass

    return default_config


def save_field_order_config(data, deps=None):
    deps = deps or {}
    _save_field_order_to_json(data)

    is_postgres_writes_enabled = deps.get('is_postgres_writes_enabled')
    get_postgres_backend = deps.get('get_postgres_backend')

    if callable(is_postgres_writes_enabled) and callable(get_postgres_backend) and is_postgres_writes_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        app_settings_table = backend['app_settings_table']
        try:
            existing = session.execute(
                select(app_settings_table.c.id).where(
                    and_(app_settings_table.c.scope == 'global', app_settings_table.c.key == 'field_order')
                )
            ).first()

            if existing:
                session.execute(
                    app_settings_table.update()
                    .where(app_settings_table.c.id == existing[0])
                    .values(value=data)
                )
            else:
                session.execute(
                    app_settings_table.insert().values(scope='global', key='field_order', value=data)
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

    def require_admin():
        # Placeholder: Replace with actual admin check logic
        # Should check for admin token/role in production
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or 'Bearer' not in auth_header:
            return jsonify({'error': 'Admin authentication required'}), 401
        # Optionally, validate token and check admin role here
        return None

    @bp.route('/admin/field-order', methods=['GET'])
    def get_field_order():
        auth_error = require_admin()
        if auth_error:
            return auth_error
        try:
            data = load_field_order_config(deps)
            return jsonify({'field_order': data})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/admin/field-order', methods=['POST', 'PUT'])
    def set_field_order():
        auth_error = require_admin()
        if auth_error:
            return auth_error
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            save_field_order_config(data, deps)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return bp
