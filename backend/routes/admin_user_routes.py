import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, g
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Role codes that are globally scoped (not tied to a specific club)
GLOBAL_ROLE_CODES = {'app_admin', 'app_owner'}


def create_admin_user_blueprint(deps):
    bp = Blueprint('admin_users', __name__)

    require_permission = deps['require_permission']
    get_postgres_backend = deps['get_postgres_backend']

    def _get_session():
        backend = get_postgres_backend()
        return backend['session_factory']()

    # -------------------------------------------------------------------------
    # GET /admin/clubs-list
    # Returns all active clubs with their database IDs for use in the grant
    # modal's club selector.  Lighter than the JSON-config /admin/clubs.
    # -------------------------------------------------------------------------
    @bp.route('/admin/clubs-list', methods=['GET'])
    def admin_clubs_list():
        auth_error = require_permission('role.assign.club')
        if auth_error:
            return auth_error

        session = _get_session()
        try:
            rows = session.execute(text(
                "SELECT id, short_name, full_name FROM clubs WHERE is_active = TRUE ORDER BY short_name"
            )).fetchall()
        finally:
            session.close()

        return jsonify({'clubs': [
            {'id': r.id, 'shortName': r.short_name, 'fullName': r.full_name}
            for r in rows
        ]})

    # -------------------------------------------------------------------------
    # GET /admin/roles
    # Returns roles the caller is permitted to assign.
    # app_owner  → all 5 roles
    # app_admin  → club-scoped roles only (user, club_admin, club_manager)
    # -------------------------------------------------------------------------
    @bp.route('/admin/roles', methods=['GET'])
    def admin_list_roles():
        auth_error = require_permission('role.assign.club')
        if auth_error:
            return auth_error

        principal = getattr(g, 'principal', None)
        effective_roles = set((principal or {}).get('effective_roles', []))
        can_assign_global = 'app_owner' in effective_roles

        session = _get_session()
        try:
            rows = session.execute(text(
                "SELECT id, code, name, scope_type FROM roles ORDER BY id"
            )).fetchall()
        finally:
            session.close()

        roles = []
        for r in rows:
            is_global = r.scope_type == 'global'
            if is_global and not can_assign_global:
                continue
            roles.append({
                'id': r.id,
                'code': r.code,
                'name': r.name,
                'scopeType': r.scope_type,
            })

        return jsonify({'roles': roles})

    # -------------------------------------------------------------------------
    # GET /admin/users
    # Returns all members who have at least one active role assignment,
    # with their full assignment list.
    # -------------------------------------------------------------------------
    @bp.route('/admin/users', methods=['GET'])
    def admin_list_users_with_roles():
        auth_error = require_permission('role.assign.club')
        if auth_error:
            return auth_error

        session = _get_session()
        try:
            rows = session.execute(text("""
                SELECT
                    m.id            AS member_id,
                    m.username,
                    m.members_name,
                    c.short_name    AS club_short_name,
                    mra.id          AS assignment_id,
                    r.code          AS role_code,
                    r.name          AS role_name,
                    r.scope_type    AS role_scope,
                    rc.id           AS role_club_id,
                    rc.short_name   AS role_club_short_name,
                    mra.granted_at
                FROM members m
                JOIN  member_role_assignments mra ON m.id  = mra.member_id
                JOIN  roles r                     ON r.id  = mra.role_id
                LEFT JOIN clubs c                 ON c.id  = m.club_id
                LEFT JOIN clubs rc                ON rc.id = mra.club_id
                WHERE mra.revoked_at IS NULL
                ORDER BY m.username, r.scope_type DESC, r.code
            """)).fetchall()
        finally:
            session.close()

        members_map = {}
        for row in rows:
            mid = row.member_id
            if mid not in members_map:
                members_map[mid] = {
                    'memberId': mid,
                    'username': row.username,
                    'membersName': row.members_name,
                    'clubShortName': row.club_short_name,
                    'assignments': [],
                }
            members_map[mid]['assignments'].append({
                'assignmentId': row.assignment_id,
                'roleCode': row.role_code,
                'roleName': row.role_name,
                'roleScope': row.role_scope,
                'roleClubId': row.role_club_id,
                'roleClubShortName': row.role_club_short_name,
                'grantedAt': row.granted_at.isoformat() if row.granted_at else None,
            })

        return jsonify({'users': list(members_map.values())})

    # -------------------------------------------------------------------------
    # GET /admin/users/search?q=<term>&limit=<n>
    # Typeahead search across all members (any club) by username or name.
    # Minimum 2-character query.
    # -------------------------------------------------------------------------
    @bp.route('/admin/users/search', methods=['GET'])
    def admin_search_users():
        auth_error = require_permission('role.assign.club')
        if auth_error:
            return auth_error

        q = (request.args.get('q') or '').strip()
        if len(q) < 2:
            return jsonify({'members': []})

        try:
            limit = min(int(request.args.get('limit', 20)), 50)
        except (TypeError, ValueError):
            limit = 20

        pattern = f'%{q}%'
        session = _get_session()
        try:
            rows = session.execute(text("""
                SELECT DISTINCT ON (m.username)
                    m.id,
                    m.username,
                    m.members_name,
                    c.short_name AS club_short_name,
                    c.id         AS club_id
                FROM members m
                LEFT JOIN clubs c ON c.id = m.club_id
                WHERE
                    LOWER(m.username)     LIKE LOWER(:pattern)
                    OR LOWER(m.members_name) LIKE LOWER(:pattern)
                ORDER BY m.username, m.id
                LIMIT :limit
            """), {'pattern': pattern, 'limit': limit}).fetchall()
        finally:
            session.close()

        return jsonify({'members': [
            {
                'memberId': r.id,
                'username': r.username,
                'membersName': r.members_name,
                'clubShortName': r.club_short_name,
                'clubId': r.club_id,
            }
            for r in rows
        ]})

    # -------------------------------------------------------------------------
    # GET /admin/users/<member_id>/roles
    # Full assignment history (active + revoked) for a single member.
    # -------------------------------------------------------------------------
    @bp.route('/admin/users/<int:member_id>/roles', methods=['GET'])
    def admin_get_user_roles(member_id):
        auth_error = require_permission('role.assign.club')
        if auth_error:
            return auth_error

        session = _get_session()
        try:
            rows = session.execute(text("""
                SELECT
                    mra.id          AS assignment_id,
                    r.code          AS role_code,
                    r.name          AS role_name,
                    r.scope_type    AS role_scope,
                    rc.short_name   AS role_club_short_name,
                    mra.granted_at,
                    mra.revoked_at,
                    gb.username     AS granted_by_username
                FROM member_role_assignments mra
                JOIN  roles r    ON r.id  = mra.role_id
                LEFT JOIN clubs rc ON rc.id = mra.club_id
                LEFT JOIN members gb ON gb.id = mra.granted_by_member_id
                WHERE mra.member_id = :member_id
                ORDER BY mra.granted_at DESC
            """), {'member_id': member_id}).fetchall()
        finally:
            session.close()

        return jsonify({'assignments': [
            {
                'assignmentId': r.assignment_id,
                'roleCode': r.role_code,
                'roleName': r.role_name,
                'roleScope': r.role_scope,
                'roleClubShortName': r.role_club_short_name,
                'grantedAt': r.granted_at.isoformat() if r.granted_at else None,
                'revokedAt': r.revoked_at.isoformat() if r.revoked_at else None,
                'grantedByUsername': r.granted_by_username,
                'isActive': r.revoked_at is None,
            }
            for r in rows
        ]})

    # -------------------------------------------------------------------------
    # POST /admin/users/<member_id>/roles
    # Grant a role to a member.
    # Body: { roleCode: str, clubId: int|null }
    # clubId is required for club-scoped roles, ignored for global roles.
    # -------------------------------------------------------------------------
    @bp.route('/admin/users/<int:member_id>/roles', methods=['POST'])
    def admin_grant_role(member_id):
        data = request.json or {}
        role_code = str(data.get('roleCode', '')).strip()
        club_id = data.get('clubId')

        if not role_code:
            return jsonify({'error': 'roleCode is required'}), 400

        is_global = role_code in GLOBAL_ROLE_CODES
        auth_error = require_permission('role.assign.global' if is_global else 'role.assign.club')
        if auth_error:
            return auth_error

        principal = getattr(g, 'principal', None)
        grantor_id = (principal or {}).get('member_id')

        session = _get_session()
        try:
            role_row = session.execute(
                text("SELECT id, scope_type FROM roles WHERE code = :code"),
                {'code': role_code}
            ).first()
            if not role_row:
                return jsonify({'error': f'Unknown role: {role_code}'}), 400

            role_id = role_row.id
            scope_type = role_row.scope_type

            if scope_type == 'club' and club_id is None:
                return jsonify({'error': 'clubId is required for club-scoped roles'}), 400

            # Global roles are never club-scoped in the assignment table
            if scope_type == 'global':
                club_id = None

            # Check for an existing active assignment
            existing = session.execute(text("""
                SELECT id FROM member_role_assignments
                WHERE member_id = :member_id
                  AND role_id   = :role_id
                  AND (
                      (:club_id IS NULL AND club_id IS NULL)
                      OR club_id = :club_id
                  )
                  AND revoked_at IS NULL
            """), {'member_id': member_id, 'role_id': role_id, 'club_id': club_id}).first()

            if existing:
                return jsonify({'error': 'Role already assigned to this member'}), 409

            now = datetime.now(timezone.utc)
            result = session.execute(text("""
                INSERT INTO member_role_assignments
                    (member_id, role_id, club_id, granted_by_member_id, granted_at)
                VALUES
                    (:member_id, :role_id, :club_id, :grantor_id, :now)
                RETURNING id
            """), {
                'member_id': member_id,
                'role_id': role_id,
                'club_id': club_id,
                'grantor_id': grantor_id,
                'now': now,
            })
            assignment_id = result.scalar()
            session.commit()

            logger.info(
                "Role '%s' granted to member %d by member %s (assignment %d)",
                role_code, member_id, grantor_id, assignment_id
            )

            return jsonify({
                'success': True,
                'assignment': {
                    'assignmentId': assignment_id,
                    'roleCode': role_code,
                    'roleScope': scope_type,
                    'clubId': club_id,
                    'grantedAt': now.isoformat(),
                },
            })

        except Exception as exc:
            session.rollback()
            logger.error("Error granting role: %s", exc, exc_info=True)
            return jsonify({'error': f'Failed to grant role: {exc}'}), 500
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # DELETE /admin/users/<member_id>/roles/<assignment_id>
    # Revoke a role assignment (soft delete: sets revoked_at).
    # Anti-lockout: a user cannot revoke their own last global admin assignment.
    # -------------------------------------------------------------------------
    @bp.route('/admin/users/<int:member_id>/roles/<int:assignment_id>', methods=['DELETE'])
    def admin_revoke_role(member_id, assignment_id):
        principal = getattr(g, 'principal', None)
        actor_id = (principal or {}).get('member_id')

        session = _get_session()
        try:
            assignment = session.execute(text("""
                SELECT mra.id, r.code AS role_code, r.scope_type, mra.revoked_at
                FROM member_role_assignments mra
                JOIN roles r ON r.id = mra.role_id
                WHERE mra.id = :assignment_id AND mra.member_id = :member_id
            """), {'assignment_id': assignment_id, 'member_id': member_id}).first()

            if not assignment:
                return jsonify({'error': 'Assignment not found'}), 404

            if assignment.revoked_at:
                return jsonify({'error': 'Assignment already revoked'}), 409

            is_global = assignment.role_code in GLOBAL_ROLE_CODES
            auth_error = require_permission('role.assign.global' if is_global else 'role.assign.club')
            if auth_error:
                return auth_error

            # Anti-lockout: prevent an admin removing their own last global role
            if actor_id == member_id and is_global:
                remaining = session.execute(text("""
                    SELECT COUNT(*) FROM member_role_assignments mra
                    JOIN roles r ON r.id = mra.role_id
                    WHERE mra.member_id = :member_id
                      AND r.code IN ('app_admin', 'app_owner')
                      AND mra.revoked_at IS NULL
                      AND mra.id != :assignment_id
                """), {'member_id': member_id, 'assignment_id': assignment_id}).scalar()
                if remaining == 0:
                    return jsonify({'error': 'Cannot revoke your own last global admin role'}), 403

            now = datetime.now(timezone.utc)
            session.execute(text("""
                UPDATE member_role_assignments
                SET revoked_at = :now
                WHERE id = :assignment_id
            """), {'now': now, 'assignment_id': assignment_id})
            session.commit()

            logger.info(
                "Assignment %d (role '%s') revoked from member %d by member %s",
                assignment_id, assignment.role_code, member_id, actor_id
            )

            return jsonify({'success': True})

        except Exception as exc:
            session.rollback()
            logger.error("Error revoking role: %s", exc, exc_info=True)
            return jsonify({'error': f'Failed to revoke role: {exc}'}), 500
        finally:
            session.close()

    return bp
