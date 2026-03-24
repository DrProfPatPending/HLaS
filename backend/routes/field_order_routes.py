import os
import json
from flask import Blueprint, jsonify, request, current_app
from functools import wraps

def create_field_order_blueprint():
    bp = Blueprint('field_order', __name__)
    FIELD_ORDER_PATH = os.path.join(os.path.dirname(__file__), '../field_order.json')

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
            with open(FIELD_ORDER_PATH, 'r') as f:
                data = json.load(f)
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
            with open(FIELD_ORDER_PATH, 'w') as f:
                json.dump(data, f, indent=2)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return bp
