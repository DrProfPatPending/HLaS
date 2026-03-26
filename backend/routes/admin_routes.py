import os
import re
import smtplib
import logging

from email.message import EmailMessage
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import select, text
from werkzeug.security import check_password_hash

logger = logging.getLogger(__name__)


def create_admin_blueprint(deps):
    bp = Blueprint('admin', __name__)

    require_permission = deps['require_permission']
    load_clubs_config = deps['load_clubs_config']
    save_clubs_config = deps['save_clubs_config']
    get_club_logo_path = deps['get_club_logo_path']
    save_uploaded_logo = deps['save_uploaded_logo']
    create_empty_club_database = deps['create_empty_club_database']
    is_postgres_writes_enabled = deps['is_postgres_writes_enabled']
    normalize_beats = deps['normalize_beats']
    get_smtp_config_for_club = deps['get_smtp_config_for_club']
    issue_member_token_pair = deps.get('issue_member_token_pair')
    load_member_roles = deps.get('load_member_roles')
    get_read_db_for_club = deps.get('get_read_db_for_club')

    @bp.route('/admin/login', methods=['POST'])
    def admin_login():
        """Authenticate admin users (members with app_admin or app_owner role)"""
        data = request.json or {}
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        # Try to authenticate against PostgreSQL central database (admin users are global)
        try:
            logger.info(f"Admin login attempt for user: {username}")
            from db import get_postgres_backend
            
            backend = get_postgres_backend()
            session = backend['session_factory']()
            
            try:
                # Query member by username; verify an app_admin/app_owner role exists via user_id
                member = session.execute(text("""
                    SELECT
                        m.id          AS member_id,
                        m.username,
                        m.members_name,
                        m.password,
                        m.club_id,
                        au.id         AS user_id
                    FROM members m
                    JOIN app_users au ON au.id = (
                        SELECT mul.user_id FROM member_user_links mul WHERE mul.member_id = m.id LIMIT 1
                    )
                    WHERE m.username = :username
                    LIMIT 1
                """), {'username': username}).first()

                if not member:
                    logger.warning(f"Admin login failed: user '{username}' not found")
                    return jsonify({'error': 'Invalid credentials'}), 401

                member_id   = member.member_id
                user_id     = member.user_id
                db_username = member.username
                member_name = member.members_name
                stored_password = member.password
                logger.info(f"Found user: {db_username} (member {member_id}, user {user_id})")

                # Check password
                if not check_password_hash(stored_password, password):
                    logger.warning(f"Admin login failed for {username}: password mismatch")
                    return jsonify({'error': 'Invalid credentials'}), 401

                logger.info(f"Password valid for {username}")

                # Verify at least one active app_admin/app_owner role assignment exists for this user
                has_admin_role = session.execute(text("""
                    SELECT 1 FROM member_role_assignments mra
                    JOIN roles r ON r.id = mra.role_id
                    WHERE mra.user_id = :user_id
                      AND r.code IN ('app_admin', 'app_owner')
                      AND mra.revoked_at IS NULL
                    LIMIT 1
                """), {'user_id': user_id}).first()

                if not has_admin_role:
                    logger.warning(f"Admin login failed: user '{username}' has no active admin role")
                    return jsonify({'error': 'Invalid credentials'}), 401

                # Load roles to get complete role list
                role_payload = load_member_roles(member_id, 'GAAFFS', user_id=user_id)
                effective_roles = role_payload.get('effective_roles', [])
                logger.info(f"Loaded roles for {username}: {effective_roles}")

                # Issue token pair (use GAAFFS as the club context for admin token)
                token_payload = issue_member_token_pair(member_id, 'GAAFFS', username, user_id=user_id, user_type="admin")
                logger.info(f"Issued token for {username}")
                
                return jsonify({
                    'success': True,
                    'user': {
                        'id': member_id,
                        'username': db_username,
                        'name': member_name,
                    },
                    'roles': effective_roles,
                    **token_payload,  # Spread token, refreshToken, expiresInSeconds, refreshExpiresInSeconds
                })
            
            finally:
                session.close()
            
        except Exception as e:
            logger.error(f"Admin login error: {str(e)}", exc_info=True)
            return jsonify({'error': f'Authentication error: {str(e)}'}), 500

    @bp.route('/admin/logout', methods=['POST'])
    def admin_logout():
        """Admin logout endpoint (no-op for now, token revocation happens client-side)"""
        return jsonify({'success': True})

    @bp.route('/admin/clubs', methods=['GET'])
    def admin_get_clubs():
        auth_error = require_permission('club.read')
        if auth_error:
            return auth_error
        return jsonify({'clubs': load_clubs_config()})

    @bp.route('/admin/clubs', methods=['POST'])
    def admin_add_club():
        auth_error = require_permission('club.create')
        if auth_error:
            return auth_error
        data = request.form if request.form else (request.json or {})
        short_name = str(data.get('shortName', '')).strip()
        if not short_name:
            return jsonify({'error': 'shortName is required'}), 400
        if not re.fullmatch(r'[A-Za-z0-9_-]+', short_name):
            return jsonify({'error': 'shortName may only contain letters, numbers, underscore, and hyphen'}), 400

        clubs = load_clubs_config()
        if any(c.get('shortName') == short_name for c in clubs):
            return jsonify({'error': f'Club "{short_name}" already exists'}), 409

        logo_url = ''
        logo_file = request.files.get('logoFile')
        logo_path = get_club_logo_path(short_name)
        if logo_file and logo_file.filename:
            try:
                logo_url = save_uploaded_logo(short_name, logo_file)
            except ValueError as exc:
                return jsonify({'error': str(exc)}), 400

        if not is_postgres_writes_enabled():
            try:
                create_empty_club_database(short_name)
            except FileExistsError as exc:
                if logo_url and os.path.exists(logo_path):
                    os.remove(logo_path)
                return jsonify({'error': str(exc)}), 409
            except FileNotFoundError as exc:
                if logo_url and os.path.exists(logo_path):
                    os.remove(logo_path)
                return jsonify({'error': str(exc)}), 500
            except Exception as exc:
                if logo_url and os.path.exists(logo_path):
                    os.remove(logo_path)
                return jsonify({'error': f'Failed to create database for {short_name}: {exc}'}), 500

        clubs.append({
            'fullName': str(data.get('fullName', short_name)).strip(),
            'shortName': short_name,
            'description': str(data.get('description', '')).strip(),
            'websiteUrl': str(data.get('websiteUrl', '')).strip(),
            'adminEmail': str(data.get('adminEmail', '')).strip(),
            'logoUrl': logo_url,
            'beats': [],
            'smtp': {
                'host': '',
                'port': 587,
                'username': '',
                'password': '',
                'fromEmail': str(data.get('adminEmail', '')).strip(),
                'fromName': f"{str(data.get('fullName', short_name)).strip()} Newsletter",
                'useSsl': False,
                'useTls': True,
            },
        })
        save_clubs_config(clubs)
        return jsonify({'success': True})

    @bp.route('/admin/clubs/<short_name>', methods=['PUT'])
    def admin_update_club(short_name):
        auth_error = require_permission('club.update', short_name)
        if auth_error:
            return auth_error
        data = request.json or {}
        clubs = load_clubs_config()
        for i, club in enumerate(clubs):
            if club.get('shortName') == short_name:
                existing_smtp = club.get('smtp', {})
                incoming_smtp = data.get('smtp', existing_smtp) or existing_smtp
                raw_smtp = incoming_smtp if isinstance(incoming_smtp, dict) else {}
                clubs[i] = {
                    'fullName': str(data.get('fullName', club.get('fullName', short_name))).strip(),
                    'shortName': short_name,
                    'description': str(data.get('description', club.get('description', ''))).strip(),
                    'websiteUrl': str(data.get('websiteUrl', club.get('websiteUrl', ''))).strip(),
                    'adminEmail': str(data.get('adminEmail', club.get('adminEmail', ''))).strip(),
                    'logoUrl': str(data.get('logoUrl', club.get('logoUrl', ''))).strip(),
                    'beats': normalize_beats(data.get('beats', club.get('beats', []))),
                    'smtp': {
                        'host': str(raw_smtp.get('host', existing_smtp.get('host', ''))).strip(),
                        'port': int(raw_smtp.get('port', existing_smtp.get('port', 587))) if str(raw_smtp.get('port', existing_smtp.get('port', 587))).isdigit() else 587,
                        'username': str(raw_smtp.get('username', existing_smtp.get('username', ''))).strip(),
                        'password': str(raw_smtp.get('password', existing_smtp.get('password', ''))).strip(),
                        'fromEmail': str(raw_smtp.get('fromEmail', existing_smtp.get('fromEmail', ''))).strip(),
                        'fromName': str(raw_smtp.get('fromName', existing_smtp.get('fromName', ''))).strip(),
                        'useSsl': bool(raw_smtp.get('useSsl', existing_smtp.get('useSsl', False))),
                        'useTls': bool(raw_smtp.get('useTls', existing_smtp.get('useTls', True))),
                    },
                }
                save_clubs_config(clubs)
                return jsonify({'success': True})
        return jsonify({'error': f'Club "{short_name}" not found'}), 404

    @bp.route('/admin/clubs/<short_name>', methods=['DELETE'])
    def admin_delete_club(short_name):
        auth_error = require_permission('club.delete')
        if auth_error:
            return auth_error
        clubs = load_clubs_config()
        updated = [c for c in clubs if c.get('shortName') != short_name]
        if len(updated) == len(clubs):
            return jsonify({'error': f'Club "{short_name}" not found'}), 404
        save_clubs_config(updated)
        return jsonify({'success': True})

    @bp.route('/admin/clubs/<short_name>/smtp', methods=['GET'])
    def admin_get_club_smtp(short_name):
        auth_error = require_permission('smtp.club.manage', short_name)
        if auth_error:
            return auth_error
        clubs = load_clubs_config()
        club = next((c for c in clubs if c.get('shortName') == short_name), None)
        if club is None:
            return jsonify({'error': f'Club "{short_name}" not found'}), 404
        smtp = club.get('smtp', {})
        return jsonify({
            'shortName': short_name,
            'smtp': {
                'host': smtp.get('host', ''),
                'port': smtp.get('port', 587),
                'username': smtp.get('username', ''),
                'passwordSet': bool(smtp.get('password', '').strip()),
                'fromEmail': smtp.get('fromEmail', ''),
                'fromName': smtp.get('fromName', ''),
                'useSsl': smtp.get('useSsl', False),
                'useTls': smtp.get('useTls', True),
            },
        })

    @bp.route('/admin/clubs/<short_name>/smtp', methods=['PUT'])
    def admin_update_club_smtp(short_name):
        auth_error = require_permission('smtp.club.manage', short_name)
        if auth_error:
            return auth_error
        data = request.json or {}
        clubs = load_clubs_config()
        for i, club in enumerate(clubs):
            if club.get('shortName') == short_name:
                existing_smtp = club.get('smtp', {}) or {}
                new_password = str(data.get('password', '')).strip()
                if not new_password:
                    new_password = existing_smtp.get('password', '')
                clubs[i]['smtp'] = {
                    'host': str(data.get('host', existing_smtp.get('host', ''))).strip(),
                    'port': int(data.get('port', existing_smtp.get('port', 587))) if str(data.get('port', existing_smtp.get('port', 587))).isdigit() else 587,
                    'username': str(data.get('username', existing_smtp.get('username', ''))).strip(),
                    'password': new_password,
                    'fromEmail': str(data.get('fromEmail', existing_smtp.get('fromEmail', ''))).strip(),
                    'fromName': str(data.get('fromName', existing_smtp.get('fromName', ''))).strip(),
                    'useSsl': bool(data.get('useSsl', existing_smtp.get('useSsl', False))),
                    'useTls': bool(data.get('useTls', existing_smtp.get('useTls', True))),
                }
                save_clubs_config(clubs)
                return jsonify({'success': True})
        return jsonify({'error': f'Club "{short_name}" not found'}), 404

    @bp.route('/admin/clubs/<short_name>/smtp/test', methods=['POST'])
    def admin_test_club_smtp(short_name):
        auth_error = require_permission('smtp.club.manage', short_name)
        if auth_error:
            return auth_error
        data = request.json or {}
        to_email = str(data.get('toEmail', '')).strip()
        if not to_email:
            return jsonify({'error': 'toEmail is required'}), 400

        smtp_cfg = get_smtp_config_for_club(short_name)
        if not smtp_cfg['host'] or not smtp_cfg['fromEmail']:
            return jsonify({'error': f'SMTP is not configured for club {short_name}'}), 503

        try:
            message = EmailMessage()
            message['Subject'] = f'HLaS SMTP Test – {short_name}'
            message['From'] = f"{smtp_cfg['fromName']} <{smtp_cfg['fromEmail']}>"
            message['To'] = to_email
            message.set_content(f'This is a test email from the HLaS application for club {short_name}.\n\nIf you received this, SMTP is configured correctly.')

            if smtp_cfg['useSsl']:
                server = smtplib.SMTP_SSL(smtp_cfg['host'], smtp_cfg['port'], timeout=20)
            else:
                server = smtplib.SMTP(smtp_cfg['host'], smtp_cfg['port'], timeout=20)

            with server:
                if not smtp_cfg['useSsl'] and smtp_cfg['useTls']:
                    server.starttls()
                if smtp_cfg['username']:
                    server.login(smtp_cfg['username'], smtp_cfg['password'])
                server.send_message(message)

            return jsonify({'success': True, 'message': f'Test email sent to {to_email}'})
        except Exception as exc:
            return jsonify({'error': f'SMTP test failed: {exc}'}), 502

    return bp
