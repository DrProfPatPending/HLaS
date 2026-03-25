import json as _json
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

    def _merge_users_in_session(session, source_user_id, target_user_id):
        if source_user_id == target_user_id:
            raise ValueError('sourceUserId and targetUserId must be different')

        source_user = session.execute(text("""
            SELECT id, username, display_name, is_active
            FROM app_users
            WHERE id = :uid
        """), {'uid': source_user_id}).first()
        target_user = session.execute(text("""
            SELECT id, username, display_name, is_active
            FROM app_users
            WHERE id = :uid
        """), {'uid': target_user_id}).first()

        if not source_user:
            raise ValueError('Source user not found')
        if not target_user:
            raise ValueError('Target user not found')
        if not source_user.is_active:
            raise ValueError('Source user is already inactive')
        if not target_user.is_active:
            raise ValueError('Target user is inactive')

        now = datetime.now(timezone.utc)

        revoked_duplicates = session.execute(text("""
            UPDATE member_role_assignments src
            SET revoked_at = :now
            FROM member_role_assignments tgt
            WHERE src.user_id = :source_user_id
              AND src.revoked_at IS NULL
              AND tgt.user_id = :target_user_id
              AND tgt.revoked_at IS NULL
              AND src.role_id = tgt.role_id
              AND (
                    (src.club_id IS NULL AND tgt.club_id IS NULL)
                    OR src.club_id = tgt.club_id
              )
            RETURNING src.id
        """), {
            'now': now,
            'source_user_id': source_user_id,
            'target_user_id': target_user_id,
        }).fetchall()

        moved_links = session.execute(text("""
            UPDATE member_user_links
            SET user_id = :target_user_id,
                is_primary = FALSE
            WHERE user_id = :source_user_id
            RETURNING id
        """), {
            'source_user_id': source_user_id,
            'target_user_id': target_user_id,
        }).fetchall()

        moved_assignments = session.execute(text("""
            UPDATE member_role_assignments
            SET user_id = :target_user_id
            WHERE user_id = :source_user_id
            RETURNING id
        """), {
            'source_user_id': source_user_id,
            'target_user_id': target_user_id,
        }).fetchall()

        moved_member_sessions = session.execute(text("""
            UPDATE member_sessions
            SET user_id = :target_user_id
            WHERE user_id = :source_user_id
              AND revoked_at IS NULL
            RETURNING token_hash
        """), {
            'source_user_id': source_user_id,
            'target_user_id': target_user_id,
        }).fetchall()

        moved_refresh_sessions = session.execute(text("""
            UPDATE member_refresh_sessions
            SET user_id = :target_user_id
            WHERE user_id = :source_user_id
              AND revoked_at IS NULL
            RETURNING refresh_token_hash
        """), {
            'source_user_id': source_user_id,
            'target_user_id': target_user_id,
        }).fetchall()

        session.execute(text("""
            UPDATE app_users
            SET
                display_name = CASE
                    WHEN COALESCE(NULLIF(display_name, ''), '') = '' THEN COALESCE(:source_display_name, display_name)
                    ELSE display_name
                END,
                email = CASE
                    WHEN COALESCE(NULLIF(email, ''), '') = '' THEN (
                        SELECT COALESCE(NULLIF(email, ''), '') FROM app_users WHERE id = :source_user_id
                    )
                    ELSE email
                END,
                updated_at = :now
            WHERE id = :target_user_id
        """), {
            'source_user_id': source_user_id,
            'target_user_id': target_user_id,
            'source_display_name': source_user.display_name,
            'now': now,
        })

        source_username = str(source_user.username or '').strip()
        source_username_archived = (
            f"{source_username}__merged__{source_user_id}" if source_username else f"merged__{source_user_id}"
        )
        session.execute(text("""
            UPDATE app_users
            SET
                is_active = FALSE,
                username = :archived_username,
                updated_at = :now
            WHERE id = :source_user_id
        """), {
            'source_user_id': source_user_id,
            'archived_username': source_username_archived,
            'now': now,
        })

        return {
            'movedLinks': len(moved_links),
            'movedAssignments': len(moved_assignments),
            'revokedDuplicateAssignments': len(revoked_duplicates),
            'movedMemberSessions': len(moved_member_sessions),
            'movedRefreshSessions': len(moved_refresh_sessions),
        }

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
    # Returns all app_users with at least one active role assignment, grouped
    # by user_id.
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
                    au.id           AS user_id,
                    au.username,
                    au.display_name,
                    mra.id          AS assignment_id,
                    r.code          AS role_code,
                    r.name          AS role_name,
                    r.scope_type    AS role_scope,
                    rc.id           AS role_club_id,
                    rc.short_name   AS role_club_short_name,
                    mra.granted_at,
                    hc.short_name   AS home_club_short_name
                FROM app_users au
                JOIN  member_role_assignments mra ON mra.user_id = au.id
                JOIN  roles r                     ON r.id  = mra.role_id
                LEFT JOIN clubs rc                ON rc.id = mra.club_id
                LEFT JOIN member_user_links hcl   ON hcl.user_id = au.id AND hcl.is_primary = TRUE
                LEFT JOIN clubs hc                ON hc.id = hcl.club_id
                WHERE mra.revoked_at IS NULL
                  AND au.is_active = TRUE
                ORDER BY au.username, r.scope_type DESC, r.code
            """)).fetchall()
        finally:
            session.close()

        users_map = {}
        for row in rows:
            uid = row.user_id
            if uid not in users_map:
                users_map[uid] = {
                    'userId': uid,
                    'username': row.username,
                    'displayName': row.display_name,
                    'homeClub': row.home_club_short_name or None,
                    'assignments': [],
                }
            users_map[uid]['assignments'].append({
                'assignmentId': row.assignment_id,
                'roleCode': row.role_code,
                'roleName': row.role_name,
                'roleScope': row.role_scope,
                'roleClubId': row.role_club_id,
                'roleClubShortName': row.role_club_short_name,
                'grantedAt': row.granted_at.isoformat() if row.granted_at else None,
            })

        return jsonify({'users': list(users_map.values())})

    # -------------------------------------------------------------------------
    # GET /admin/users/search?q=<term>&limit=<n>
    # Typeahead search across app_users by username or display_name.
    # Returns userId, username, displayName, and a clubs array.
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
                SELECT
                    au.id           AS user_id,
                    au.username,
                    au.display_name,
                    json_agg(
                        json_build_object('id', c.id, 'shortName', c.short_name)
                        ORDER BY c.short_name
                    ) AS clubs
                FROM app_users au
                JOIN member_user_links mul ON mul.user_id = au.id
                JOIN clubs c ON c.id = mul.club_id
                                WHERE au.username != ''
                                    AND au.is_active = TRUE
                  AND (
                      LOWER(au.username)     LIKE LOWER(:pattern)
                      OR LOWER(au.display_name) LIKE LOWER(:pattern)
                  )
                GROUP BY au.id, au.username, au.display_name
                ORDER BY au.username
                LIMIT :limit
            """), {'pattern': pattern, 'limit': limit}).fetchall()
        finally:
            session.close()

        members = []
        for r in rows:
            clubs_raw = r.clubs
            clubs = clubs_raw if isinstance(clubs_raw, list) else _json.loads(clubs_raw)
            members.append({
                'userId': r.user_id,
                'username': r.username,
                'displayName': r.display_name,
                'clubs': clubs,
            })
        return jsonify({'members': members})

    # -------------------------------------------------------------------------
    # GET /admin/users/<user_id>/roles
    # Full assignment history (active + revoked) for a single user.
    # -------------------------------------------------------------------------
    @bp.route('/admin/users/<int:user_id>/roles', methods=['GET'])
    def admin_get_user_roles(user_id):
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
                WHERE mra.user_id = :user_id
                ORDER BY mra.granted_at DESC
            """), {'user_id': user_id}).fetchall()
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
    # POST /admin/users/<user_id>/roles
    # Grant a role to a user.
    # Body: { roleCode: str, clubId: int|null }
    # clubId is required for club-scoped roles, ignored for global roles.
    # -------------------------------------------------------------------------
    @bp.route('/admin/users/<int:user_id>/roles', methods=['POST'])
    def admin_grant_role(user_id):
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
        grantor_member_id = (principal or {}).get('member_id')

        session = _get_session()
        try:
            # Verify target user exists and is active
            user_row = session.execute(text(
                "SELECT id FROM app_users WHERE id = :uid AND is_active = TRUE"
            ), {'uid': user_id}).first()
            if not user_row:
                return jsonify({'error': 'User not found or inactive'}), 404

            # Fetch role
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

            # Validate club membership for club-scoped roles.
            if scope_type == 'club':
                link_exists = session.execute(text("""
                    SELECT 1 FROM member_user_links
                    WHERE user_id = :uid AND club_id = :club_id
                """), {'uid': user_id, 'club_id': club_id}).first()
                if not link_exists:
                    return jsonify({'error': 'User is not a member of the selected club'}), 400
            else:
                # Global role: confirm user has at least one member link.
                link_exists = session.execute(text(
                    "SELECT 1 FROM member_user_links WHERE user_id = :uid LIMIT 1"
                ), {'uid': user_id}).first()
                if not link_exists:
                    return jsonify({'error': 'User has no member links'}), 400

            # Check for an existing active assignment (keyed on user_id)
            existing = session.execute(text("""

            if club_id is None:
                existing = db.session.execute(text("""
                    SELECT id FROM member_role_assignments
                    WHERE user_id  = :user_id
                      AND role_id  = :role_id
                      AND club_id IS NULL
                      AND revoked_at IS NULL
                """), {'user_id': user_id, 'role_id': role_id}).first()
            else:
                existing = db.session.execute(text("""
                    SELECT id FROM member_role_assignments
                    WHERE user_id  = :user_id
                      AND role_id  = :role_id
                      AND club_id = :club_id
                      AND revoked_at IS NULL
                """), {'user_id': user_id, 'role_id': role_id, 'club_id': club_id}).first()

            if existing:
                return jsonify({'error': 'Role already assigned to this user'}), 409

            now = datetime.now(timezone.utc)
            result = session.execute(text("""
                INSERT INTO member_role_assignments
                    (user_id, role_id, club_id, granted_by_member_id, granted_at)
                VALUES
                    (:user_id, :role_id, :club_id, :grantor_id, :now)
                RETURNING id
            """), {
                'user_id': user_id,
                'role_id': role_id,
                'club_id': club_id,
                'grantor_id': grantor_member_id,
                'now': now,
            })
            assignment_id = result.scalar()
            session.commit()

            logger.info(
                "Role '%s' granted to user %d by member %s (assignment %d)",
                role_code, user_id, grantor_member_id, assignment_id
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
    # DELETE /admin/users/<user_id>/roles/<assignment_id>
    # Revoke a role assignment (soft delete: sets revoked_at).
    # Anti-lockout: a user cannot revoke their own last global admin assignment.
    # -------------------------------------------------------------------------
    @bp.route('/admin/users/<int:user_id>/roles/<int:assignment_id>', methods=['DELETE'])
    def admin_revoke_role(user_id, assignment_id):
        principal = getattr(g, 'principal', None)
        actor_user_id = (principal or {}).get('user_id')

        session = _get_session()
        try:
            assignment = session.execute(text("""
                SELECT mra.id, r.code AS role_code, r.scope_type, mra.revoked_at
                FROM member_role_assignments mra
                JOIN roles r ON r.id = mra.role_id
                WHERE mra.id = :assignment_id AND mra.user_id = :user_id
            """), {'assignment_id': assignment_id, 'user_id': user_id}).first()

            if not assignment:
                return jsonify({'error': 'Assignment not found'}), 404

            if assignment.revoked_at:
                return jsonify({'error': 'Assignment already revoked'}), 409

            is_global = assignment.role_code in GLOBAL_ROLE_CODES
            auth_error = require_permission('role.assign.global' if is_global else 'role.assign.club')
            if auth_error:
                return auth_error

            # Anti-lockout: prevent an admin removing their own last global role
            if actor_user_id == user_id and is_global:
                remaining = session.execute(text("""
                    SELECT COUNT(*) FROM member_role_assignments mra
                    JOIN roles r ON r.id = mra.role_id
                    WHERE mra.user_id = :user_id
                      AND r.code IN ('app_admin', 'app_owner')
                      AND mra.revoked_at IS NULL
                      AND mra.id != :assignment_id
                """), {'user_id': user_id, 'assignment_id': assignment_id}).scalar()
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
                "Assignment %d (role '%s') revoked from user %d by user %s",
                assignment_id, assignment.role_code, user_id, actor_user_id
            )

            return jsonify({'success': True})

        except Exception as exc:
            session.rollback()
            logger.error("Error revoking role: %s", exc, exc_info=True)
            return jsonify({'error': f'Failed to revoke role: {exc}'}), 500
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # POST /admin/users/merge
    # Merge a source app_user into a target app_user.
    # Body: { sourceUserId: int, targetUserId: int }
    #
    # Effects (single transaction):
    # - Moves member_user_links from source -> target
    # - Re-keys role assignments source.user_id -> target.user_id
    # - Reassigns active member/refresh sessions source.user_id -> target.user_id
    # - Deactivates source app_user
    # -------------------------------------------------------------------------
    @bp.route('/admin/users/merge', methods=['POST'])
    def admin_merge_users():
        auth_error = require_permission('role.assign.global')
        if auth_error:
            return auth_error

        data = request.json or {}
        try:
            source_user_id = int(data.get('sourceUserId'))
            target_user_id = int(data.get('targetUserId'))
        except (TypeError, ValueError):
            return jsonify({'error': 'sourceUserId and targetUserId must be integers'}), 400

        if source_user_id == target_user_id:
            return jsonify({'error': 'sourceUserId and targetUserId must be different'}), 400

        session = _get_session()
        try:
            summary = _merge_users_in_session(session, source_user_id, target_user_id)

            session.commit()

            logger.info(
                "Merged app_user %s into %s (links=%s assignments=%s dup_revoked=%s member_sessions=%s refresh_sessions=%s)",
                source_user_id,
                target_user_id,
                summary['movedLinks'],
                summary['movedAssignments'],
                summary['revokedDuplicateAssignments'],
                summary['movedMemberSessions'],
                summary['movedRefreshSessions'],
            )

            return jsonify({
                'success': True,
                'sourceUserId': source_user_id,
                'targetUserId': target_user_id,
                'summary': summary,
            })

        except ValueError as exc:
            session.rollback()
            error = str(exc)
            if error == 'Source user not found' or error == 'Target user not found':
                return jsonify({'error': error}), 404
            if error == 'Source user is already inactive':
                return jsonify({'error': error}), 409
            return jsonify({'error': error}), 400

        except Exception as exc:
            session.rollback()
            logger.error("Error merging users: %s", exc, exc_info=True)
            return jsonify({'error': f'Failed to merge users: {exc}'}), 500
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # POST /admin/users/merge/cleanup
    # Auto-merge safe duplicate active users that share normalized email and
    # either normalized username or display_name.
    # Body: { dryRun?: bool }
    # -------------------------------------------------------------------------
    @bp.route('/admin/users/merge/cleanup', methods=['POST'])
    def admin_merge_cleanup():
        auth_error = require_permission('role.assign.global')
        if auth_error:
            return auth_error

        data = request.json or {}
        dry_run = bool(data.get('dryRun', True))

        session = _get_session()
        try:
            rows = session.execute(text("""
                SELECT
                    au.id,
                    au.username,
                    au.display_name,
                    au.email,
                    COALESCE(link_counts.link_count, 0) AS link_count,
                    COALESCE(assign_counts.active_assignment_count, 0) AS active_assignment_count,
                    COALESCE(sess_counts.active_member_session_count, 0) AS active_member_session_count,
                    COALESCE(refresh_counts.active_refresh_session_count, 0) AS active_refresh_session_count
                FROM app_users au
                LEFT JOIN (
                    SELECT user_id, COUNT(*) AS link_count
                    FROM member_user_links
                    GROUP BY user_id
                ) link_counts ON link_counts.user_id = au.id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) AS active_assignment_count
                    FROM member_role_assignments
                    WHERE revoked_at IS NULL
                    GROUP BY user_id
                ) assign_counts ON assign_counts.user_id = au.id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) AS active_member_session_count
                    FROM member_sessions
                    WHERE revoked_at IS NULL
                    GROUP BY user_id
                ) sess_counts ON sess_counts.user_id = au.id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) AS active_refresh_session_count
                    FROM member_refresh_sessions
                    WHERE revoked_at IS NULL
                    GROUP BY user_id
                ) refresh_counts ON refresh_counts.user_id = au.id
                WHERE au.is_active = TRUE
                ORDER BY au.id
            """)).fetchall()

            users = []
            by_email = {}
            for row in rows:
                username_key = str(row.username or '').strip().lower()
                display_name_key = str(row.display_name or '').strip().lower()
                email_key = str(row.email or '').strip().lower()
                score = (
                    int(row.link_count or 0) * 1000
                    + int(row.active_assignment_count or 0) * 100
                    + int(row.active_member_session_count or 0) * 10
                    + int(row.active_refresh_session_count or 0)
                )
                record = {
                    'id': int(row.id),
                    'username': str(row.username or '').strip(),
                    'display_name': str(row.display_name or '').strip(),
                    'usernameKey': username_key,
                    'displayNameKey': display_name_key,
                    'emailKey': email_key,
                    'score': score,
                }
                users.append(record)
                if email_key:
                    by_email.setdefault(email_key, []).append(record)

            candidate_groups = [group for group in by_email.values() if len(group) > 1]

            planned = []
            skipped = []
            merged_user_ids = set()

            for group in candidate_groups:
                group_sorted = sorted(group, key=lambda u: (-u['score'], u['id']))
                target = group_sorted[0]
                for source in group_sorted[1:]:
                    if source['id'] in merged_user_ids or target['id'] in merged_user_ids:
                        skipped.append({
                            'sourceUserId': source['id'],
                            'targetUserId': target['id'],
                            'reason': 'Already merged in this run',
                        })
                        continue

                    same_username = bool(source['usernameKey']) and source['usernameKey'] == target['usernameKey']
                    same_display = bool(source['displayNameKey']) and source['displayNameKey'] == target['displayNameKey']
                    if not (same_username or same_display):
                        skipped.append({
                            'sourceUserId': source['id'],
                            'targetUserId': target['id'],
                            'reason': 'Email matches but username/display_name do not match',
                        })
                        continue

                    planned.append({
                        'sourceUserId': source['id'],
                        'sourceUsername': source.get('username', ''),
                        'sourceDisplayName': source.get('display_name', ''),
                        'targetUserId': target['id'],
                        'targetUsername': target.get('username', ''),
                        'targetDisplayName': target.get('display_name', ''),
                    })
                    if not dry_run:
                        summary = _merge_users_in_session(session, source['id'], target['id'])
                        merged_user_ids.add(source['id'])
                        planned[-1]['summary'] = summary

            if not dry_run:
                session.commit()

            return jsonify({
                'success': True,
                'dryRun': dry_run,
                'plannedMerges': planned,
                'skipped': skipped,
                'mergeCount': len(planned),
            })

        except Exception as exc:
            session.rollback()
            logger.error("Error running merge cleanup: %s", exc, exc_info=True)
            return jsonify({'error': f'Failed to run merge cleanup: {exc}'}), 500
        finally:
            session.close()

    return bp
