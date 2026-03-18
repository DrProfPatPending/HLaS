from flask import g, jsonify
from sqlalchemy import and_, select

from auth.session_tokens import extract_bearer_token, get_member_session_from_token
from db import get_postgres_backend, is_postgres_reads_enabled
from security.permissions import DEFAULT_ROLE_CODE, has_permission, list_permissions


GLOBAL_ADMIN_ROLES = {'app_admin', 'app_owner'}


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_club_id(session, clubs_table, club_short_name):
    normalized_club = str(club_short_name or '').strip()
    if not normalized_club:
        return None

    return session.execute(
        select(clubs_table.c.id).where(
            and_(clubs_table.c.short_name == normalized_club, clubs_table.c.is_active.is_(True))
        )
    ).scalar_one_or_none()


def load_member_roles(member_id, club_short_name=''):
    member_id_int = _safe_int(member_id)
    if member_id_int is None:
        return {
            'global_roles': [],
            'club_roles': [DEFAULT_ROLE_CODE],
            'effective_roles': [DEFAULT_ROLE_CODE],
            'permissions': list_permissions({DEFAULT_ROLE_CODE}),
        }

    if not is_postgres_reads_enabled():
        return {
            'global_roles': [],
            'club_roles': [DEFAULT_ROLE_CODE],
            'effective_roles': [DEFAULT_ROLE_CODE],
            'permissions': list_permissions({DEFAULT_ROLE_CODE}),
        }

    backend = get_postgres_backend()
    session = backend['session_factory']()
    roles_table = backend['roles_table']
    assignments_table = backend['member_role_assignments_table']
    clubs_table = backend['clubs_table']

    global_roles = set()
    club_roles = set()

    try:
        target_club_id = _resolve_club_id(session, clubs_table, club_short_name)

        rows = session.execute(
            select(
                roles_table.c.code,
                roles_table.c.scope_type,
                assignments_table.c.club_id,
            ).select_from(
                assignments_table.join(roles_table, assignments_table.c.role_id == roles_table.c.id)
            ).where(
                and_(
                    assignments_table.c.member_id == member_id_int,
                    assignments_table.c.revoked_at.is_(None),
                )
            )
        ).fetchall()

        for row in rows:
            role_code = str(row.code or '').strip()
            if not role_code:
                continue

            scope_type = str(row.scope_type or '').strip().lower()
            assignment_club_id = row.club_id

            if scope_type == 'global' or assignment_club_id is None:
                global_roles.add(role_code)
                continue

            if target_club_id is not None and assignment_club_id == target_club_id:
                club_roles.add(role_code)
    finally:
        session.close()

    effective_roles = {DEFAULT_ROLE_CODE}
    effective_roles.update(global_roles)
    effective_roles.update(club_roles)

    return {
        'global_roles': sorted(global_roles),
        'club_roles': sorted(club_roles),
        'effective_roles': sorted(effective_roles),
        'permissions': list_permissions(effective_roles),
    }


def get_current_principal(club_short_name=''):
    requested_club = str(club_short_name or '').strip()

    existing_principal = getattr(g, 'principal', None)
    if existing_principal is not None:
        existing_scope = str(existing_principal.get('scope_club_short_name', '')).strip()
        if existing_scope == requested_club:
            return existing_principal

    token_value = extract_bearer_token()
    if not token_value:
        return None

    member_session = get_member_session_from_token(token_value)
    if member_session is None:
        return None

    session_club = str(member_session.get('club_short_name', '')).strip()
    scope_club = requested_club or session_club
    roles_info = load_member_roles(member_session.get('member_id'), scope_club)

    principal = {
        'member_id': _safe_int(member_session.get('member_id')),
        'username': str(member_session.get('username', '')).strip(),
        'club_short_name': session_club,
        'scope_club_short_name': scope_club,
        'global_roles': roles_info['global_roles'],
        'club_roles': roles_info['club_roles'],
        'effective_roles': roles_info['effective_roles'],
        'permissions': roles_info['permissions'],
    }

    g.member_session = member_session
    g.principal = principal
    return principal


def require_authenticated(club_short_name=''):
    principal = get_current_principal(club_short_name)
    if principal is None:
        return jsonify({'error': 'Unauthorized'}), 401

    expected_club = str(club_short_name or '').strip()
    actual_club = str(principal.get('club_short_name', '')).strip()
    effective_roles = set(principal.get('effective_roles', []))

    if expected_club and actual_club and expected_club != actual_club and not effective_roles.intersection(GLOBAL_ADMIN_ROLES):
        return jsonify({'error': 'Forbidden for selected club'}), 403

    return None


def require_permission(permission, club_short_name=''):
    auth_error = require_authenticated(club_short_name)
    if auth_error is not None:
        return auth_error

    principal = getattr(g, 'principal', None)
    role_codes = set(principal.get('effective_roles', [])) if principal else set()

    if not has_permission(role_codes, permission):
        return jsonify({'error': 'Forbidden'}), 403

    return None


def require_self_or_permission(target_member_id, permission, club_short_name=''):
    auth_error = require_authenticated(club_short_name)
    if auth_error is not None:
        return auth_error

    principal = getattr(g, 'principal', None)
    principal_member_id = _safe_int((principal or {}).get('member_id'))
    target_member_id_int = _safe_int(target_member_id)

    if principal_member_id is not None and target_member_id_int is not None and principal_member_id == target_member_id_int:
        return None

    role_codes = set(principal.get('effective_roles', [])) if principal else set()
    if has_permission(role_codes, permission):
        return None

    return jsonify({'error': 'Forbidden'}), 403
