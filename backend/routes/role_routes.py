from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, func, or_, select


ROLE_RANK = {
    'user': 1,
    'committee': 2,
    'club_admin': 2,
    'club_manager': 3,
    'app_admin': 4,
    'app_owner': 5,
}


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value, default=False):
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {'1', 'true', 'yes', 'on'}:
        return True
    if text in {'0', 'false', 'no', 'off'}:
        return False
    return default


def create_role_blueprint(deps):
    bp = Blueprint('roles', __name__)

    is_postgres_writes_enabled = deps['is_postgres_writes_enabled']
    get_postgres_backend = deps['get_postgres_backend']
    require_authenticated = deps['require_authenticated']
    require_permission = deps['require_permission']
    get_current_principal = deps['get_current_principal']
    load_member_roles = deps['load_member_roles']

    def _require_postgres():
        if not is_postgres_writes_enabled():
            return jsonify({'error': 'RBAC role management requires PostgreSQL mode'}), 503
        return None

    def _max_role_rank(role_codes):
        if not role_codes:
            return 0
        return max(ROLE_RANK.get(str(role_code), 0) for role_code in role_codes)

    def _ensure_assignable(principal, target_role_code):
        actor_rank = _max_role_rank(principal.get('effective_roles', []))
        requested_rank = ROLE_RANK.get(str(target_role_code), 0)
        if requested_rank <= 0:
            return jsonify({'error': 'Invalid role'}), 400
        if actor_rank < requested_rank:
            return jsonify({'error': 'Forbidden to grant this role'}), 403
        return None

    def _resolve_member(session, members_table, payload):
        member_id = _safe_int(payload.get('memberId'))
        username = str(payload.get('username', '')).strip()
        email = str(payload.get('email', '')).strip()

        if member_id is not None:
            return session.execute(
                select(
                    members_table.c.id,
                    members_table.c.username,
                    members_table.c.email,
                    members_table.c.members_name,
                ).where(members_table.c.id == member_id)
            ).first()

        filters = []
        if username:
            filters.append(members_table.c.username == username)
        if email:
            filters.append(members_table.c.email == email)

        if not filters:
            return None

        return session.execute(
            select(
                members_table.c.id,
                members_table.c.username,
                members_table.c.email,
                members_table.c.members_name,
            ).where(or_(*filters)).limit(1)
        ).first()

    def _resolve_club(session, clubs_table, short_name):
        normalized = str(short_name or '').strip()
        if not normalized:
            return None

        return session.execute(
            select(clubs_table.c.id, clubs_table.c.short_name).where(
                and_(clubs_table.c.short_name == normalized, clubs_table.c.is_active.is_(True))
            )
        ).first()

    def _count_active_app_owners(session, roles_table, assignments_table):
        return session.execute(
            select(func.count()).select_from(
                assignments_table.join(roles_table, assignments_table.c.role_id == roles_table.c.id)
            ).where(
                and_(
                    roles_table.c.code == 'app_owner',
                    assignments_table.c.revoked_at.is_(None),
                )
            )
        ).scalar_one()

    def _serialize_assignment_row(row):
        return {
            'assignmentId': row.assignment_id,
            'memberId': row.member_id,
            'username': row.username or '',
            'memberName': row.member_name or '',
            'email': row.email or '',
            'roleId': row.role_id,
            'roleCode': row.role_code,
            'roleName': row.role_name,
            'scopeType': row.scope_type,
            'clubId': row.club_id,
            'clubShortName': row.club_short_name or '',
            'grantedByMemberId': row.granted_by_member_id,
            'grantedAt': row.granted_at.isoformat() if row.granted_at is not None else None,
            'revokedAt': row.revoked_at.isoformat() if row.revoked_at is not None else None,
        }

    @bp.route('/me/roles', methods=['GET'])
    def get_my_roles():
        club = request.args.get('club', '')
        auth_error = require_authenticated(club)
        if auth_error:
            return auth_error

        principal = get_current_principal(club)
        if principal is None:
            return jsonify({'error': 'Unauthorized'}), 401

        return jsonify({
            'memberId': principal.get('member_id'),
            'username': principal.get('username', ''),
            'clubShortName': principal.get('club_short_name', ''),
            'scopeClubShortName': principal.get('scope_club_short_name', ''),
            'globalRoles': principal.get('global_roles', []),
            'clubRoles': principal.get('club_roles', []),
            'effectiveRoles': principal.get('effective_roles', []),
            'permissions': principal.get('permissions', []),
        })

    @bp.route('/admin/roles/assignments', methods=['GET'])
    def list_global_role_assignments():
        db_error = _require_postgres()
        if db_error:
            return db_error

        auth_error = require_permission('role.assign.global')
        if auth_error:
            return auth_error

        include_revoked = _as_bool(request.args.get('includeRevoked'), default=False)

        backend = get_postgres_backend()
        session = backend['session_factory']()
        members_table = backend['members_table']
        roles_table = backend['roles_table']
        assignments_table = backend['member_role_assignments_table']
        clubs_table = backend['clubs_table']
        links_table = backend['member_user_links_table']

        try:
            query = select(
                assignments_table.c.id.label('assignment_id'),
                members_table.c.id.label('member_id'),
                members_table.c.username,
                members_table.c.members_name.label('member_name'),
                members_table.c.email,
                roles_table.c.id.label('role_id'),
                roles_table.c.code.label('role_code'),
                roles_table.c.name.label('role_name'),
                roles_table.c.scope_type,
                assignments_table.c.club_id,
                clubs_table.c.short_name.label('club_short_name'),
                assignments_table.c.granted_by_member_id,
                assignments_table.c.granted_at,
                assignments_table.c.revoked_at,
            ).select_from(
                assignments_table
                .join(roles_table, assignments_table.c.role_id == roles_table.c.id)
                .outerjoin(
                    links_table,
                    and_(
                        assignments_table.c.user_id == links_table.c.user_id,
                        links_table.c.is_primary.is_(True),
                    ),
                )
                .outerjoin(members_table, links_table.c.member_id == members_table.c.id)
                .outerjoin(clubs_table, assignments_table.c.club_id == clubs_table.c.id)
            ).where(roles_table.c.scope_type == 'global')

            if not include_revoked:
                query = query.where(assignments_table.c.revoked_at.is_(None))

            query = query.order_by(assignments_table.c.granted_at.desc(), assignments_table.c.id.desc())
            rows = session.execute(query).fetchall()
        finally:
            session.close()

        return jsonify({'assignments': [_serialize_assignment_row(row) for row in rows]})

    @bp.route('/admin/roles/assignments/club/<short_name>', methods=['GET'])
    def list_club_role_assignments(short_name):
        db_error = _require_postgres()
        if db_error:
            return db_error

        auth_error = require_permission('role.assign.club', short_name)
        if auth_error:
            return auth_error

        include_revoked = _as_bool(request.args.get('includeRevoked'), default=False)

        backend = get_postgres_backend()
        session = backend['session_factory']()
        members_table = backend['members_table']
        roles_table = backend['roles_table']
        assignments_table = backend['member_role_assignments_table']
        clubs_table = backend['clubs_table']
        links_table = backend['member_user_links_table']

        try:
            club_row = _resolve_club(session, clubs_table, short_name)
            if club_row is None:
                return jsonify({'error': f'Club "{short_name}" not found'}), 404

            query = select(
                assignments_table.c.id.label('assignment_id'),
                members_table.c.id.label('member_id'),
                members_table.c.username,
                members_table.c.members_name.label('member_name'),
                members_table.c.email,
                roles_table.c.id.label('role_id'),
                roles_table.c.code.label('role_code'),
                roles_table.c.name.label('role_name'),
                roles_table.c.scope_type,
                assignments_table.c.club_id,
                clubs_table.c.short_name.label('club_short_name'),
                assignments_table.c.granted_by_member_id,
                assignments_table.c.granted_at,
                assignments_table.c.revoked_at,
            ).select_from(
                assignments_table
                .join(roles_table, assignments_table.c.role_id == roles_table.c.id)
                .outerjoin(
                    links_table,
                    and_(
                        assignments_table.c.user_id == links_table.c.user_id,
                        assignments_table.c.club_id == links_table.c.club_id,
                    ),
                )
                .outerjoin(members_table, links_table.c.member_id == members_table.c.id)
                .outerjoin(clubs_table, assignments_table.c.club_id == clubs_table.c.id)
            ).where(
                and_(
                    roles_table.c.scope_type == 'club',
                    assignments_table.c.club_id == club_row.id,
                )
            )

            if not include_revoked:
                query = query.where(assignments_table.c.revoked_at.is_(None))

            query = query.order_by(assignments_table.c.granted_at.desc(), assignments_table.c.id.desc())
            rows = session.execute(query).fetchall()
        finally:
            session.close()

        return jsonify({'club': club_row.short_name, 'assignments': [_serialize_assignment_row(row) for row in rows]})

    @bp.route('/admin/roles/assignments', methods=['POST'])
    def grant_global_role_assignment():
        db_error = _require_postgres()
        if db_error:
            return db_error

        auth_error = require_permission('role.assign.global')
        if auth_error:
            return auth_error

        principal = get_current_principal()
        data = request.json or {}
        role_code = str(data.get('roleCode', '')).strip()

        if not role_code:
            return jsonify({'error': 'roleCode is required'}), 400

        rank_error = _ensure_assignable(principal or {}, role_code)
        if rank_error:
            return rank_error

        backend = get_postgres_backend()
        session = backend['session_factory']()
        members_table = backend['members_table']
        roles_table = backend['roles_table']
        assignments_table = backend['member_role_assignments_table']
        audit_table = backend['security_audit_log_table']

        try:
            target_member = _resolve_member(session, members_table, data)
            if target_member is None:
                return jsonify({'error': 'Target member not found (provide memberId, username, or email)'}), 404

            # Resolve the user account for this member.
            links_table = backend['member_user_links_table']
            link_row = session.execute(
                select(links_table.c.user_id).where(links_table.c.member_id == target_member.id)
            ).first()
            if link_row is None:
                return jsonify({'error': 'Target member has no associated user account'}), 400
            target_user_id = link_row.user_id

            role_row = session.execute(
                select(roles_table.c.id, roles_table.c.code, roles_table.c.name, roles_table.c.scope_type).where(
                    roles_table.c.code == role_code
                )
            ).first()
            if role_row is None:
                return jsonify({'error': f'Role "{role_code}" not found'}), 404
            if str(role_row.scope_type) != 'global':
                return jsonify({'error': f'Role "{role_code}" is not a global role'}), 400

            existing = session.execute(
                select(assignments_table.c.id).where(
                    and_(
                        assignments_table.c.user_id == target_user_id,
                        assignments_table.c.role_id == role_row.id,
                        assignments_table.c.club_id.is_(None),
                        assignments_table.c.revoked_at.is_(None),
                    )
                )
            ).first()
            if existing is not None:
                return jsonify({'error': 'Assignment already exists'}), 409

            insert_result = session.execute(
                assignments_table.insert().values(
                    user_id=target_user_id,
                    role_id=role_row.id,
                    club_id=None,
                    granted_by_member_id=(principal or {}).get('member_id'),
                ).returning(assignments_table.c.id)
            )
            assignment_id = insert_result.scalar_one()

            session.execute(
                audit_table.insert().values(
                    actor_member_id=(principal or {}).get('member_id'),
                    action='role.grant',
                    target_type='role_assignment',
                    target_id=assignment_id,
                    club_id=None,
                    metadata={
                        'roleCode': role_row.code,
                        'memberId': target_member.id,
                        'scope': 'global',
                    },
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return jsonify({
            'success': True,
            'assignmentId': assignment_id,
            'roleCode': role_row.code,
            'scopeType': 'global',
            'memberId': target_member.id,
        }), 201

    @bp.route('/admin/roles/assignments/club/<short_name>', methods=['POST'])
    def grant_club_role_assignment(short_name):
        db_error = _require_postgres()
        if db_error:
            return db_error

        auth_error = require_permission('role.assign.club', short_name)
        if auth_error:
            return auth_error

        principal = get_current_principal(short_name)
        data = request.json or {}
        role_code = str(data.get('roleCode', '')).strip()

        if not role_code:
            return jsonify({'error': 'roleCode is required'}), 400

        rank_error = _ensure_assignable(principal or {}, role_code)
        if rank_error:
            return rank_error

        backend = get_postgres_backend()
        session = backend['session_factory']()
        members_table = backend['members_table']
        roles_table = backend['roles_table']
        assignments_table = backend['member_role_assignments_table']
        clubs_table = backend['clubs_table']
        audit_table = backend['security_audit_log_table']

        try:
            club_row = _resolve_club(session, clubs_table, short_name)
            if club_row is None:
                return jsonify({'error': f'Club "{short_name}" not found'}), 404

            target_member = _resolve_member(session, members_table, data)
            if target_member is None:
                return jsonify({'error': 'Target member not found (provide memberId, username, or email)'}), 404

            # Resolve the user account for this member in this club.
            links_table = backend['member_user_links_table']
            link_row = session.execute(
                select(links_table.c.user_id).where(
                    and_(
                        links_table.c.member_id == target_member.id,
                        links_table.c.club_id == club_row.id,
                    )
                )
            ).first()
            if link_row is None:
                return jsonify({'error': 'Target member is not linked to this club'}), 400
            target_user_id = link_row.user_id

            role_row = session.execute(
                select(roles_table.c.id, roles_table.c.code, roles_table.c.name, roles_table.c.scope_type).where(
                    roles_table.c.code == role_code
                )
            ).first()
            if role_row is None:
                return jsonify({'error': f'Role "{role_code}" not found'}), 404
            if str(role_row.scope_type) != 'club':
                return jsonify({'error': f'Role "{role_code}" is not a club-scoped role'}), 400

            existing = session.execute(
                select(assignments_table.c.id).where(
                    and_(
                        assignments_table.c.user_id == target_user_id,
                        assignments_table.c.role_id == role_row.id,
                        assignments_table.c.club_id == club_row.id,
                        assignments_table.c.revoked_at.is_(None),
                    )
                )
            ).first()
            if existing is not None:
                return jsonify({'error': 'Assignment already exists'}), 409

            insert_result = session.execute(
                assignments_table.insert().values(
                    user_id=target_user_id,
                    role_id=role_row.id,
                    club_id=club_row.id,
                    granted_by_member_id=(principal or {}).get('member_id'),
                ).returning(assignments_table.c.id)
            )
            assignment_id = insert_result.scalar_one()

            session.execute(
                audit_table.insert().values(
                    actor_member_id=(principal or {}).get('member_id'),
                    action='role.grant',
                    target_type='role_assignment',
                    target_id=assignment_id,
                    club_id=club_row.id,
                    metadata={
                        'roleCode': role_row.code,
                        'memberId': target_member.id,
                        'scope': 'club',
                        'clubShortName': club_row.short_name,
                    },
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return jsonify({
            'success': True,
            'assignmentId': assignment_id,
            'roleCode': role_row.code,
            'scopeType': 'club',
            'clubShortName': club_row.short_name,
            'memberId': target_member.id,
        }), 201

    @bp.route('/admin/roles/assignments/<int:assignment_id>', methods=['DELETE'])
    def revoke_role_assignment(assignment_id):
        db_error = _require_postgres()
        if db_error:
            return db_error

        auth_error = require_authenticated()
        if auth_error:
            return auth_error

        principal = get_current_principal()

        backend = get_postgres_backend()
        session = backend['session_factory']()
        roles_table = backend['roles_table']
        assignments_table = backend['member_role_assignments_table']
        clubs_table = backend['clubs_table']
        audit_table = backend['security_audit_log_table']

        try:
            row = session.execute(
                select(
                    assignments_table.c.id,
                    assignments_table.c.user_id,
                    assignments_table.c.club_id,
                    assignments_table.c.revoked_at,
                    roles_table.c.code.label('role_code'),
                    roles_table.c.scope_type,
                    clubs_table.c.short_name.label('club_short_name'),
                ).select_from(
                    assignments_table
                    .join(roles_table, assignments_table.c.role_id == roles_table.c.id)
                    .outerjoin(clubs_table, assignments_table.c.club_id == clubs_table.c.id)
                ).where(assignments_table.c.id == assignment_id)
            ).first()

            if row is None:
                return jsonify({'error': 'Assignment not found'}), 404

            if row.revoked_at is not None:
                return jsonify({'error': 'Assignment already revoked'}), 409

            if str(row.scope_type) == 'global':
                permission_error = require_permission('role.assign.global')
            else:
                permission_error = require_permission('role.assign.club', row.club_short_name or '')
            if permission_error:
                return permission_error

            # Safety: prevent removing the last active app_owner role.
            if str(row.role_code) == 'app_owner':
                active_owner_count = _count_active_app_owners(session, roles_table, assignments_table)
                if active_owner_count <= 1:
                    return jsonify({'error': 'Cannot revoke the last active app_owner assignment'}), 409

            session.execute(
                assignments_table.update().where(assignments_table.c.id == assignment_id).values(
                    revoked_at=func.now()
                )
            )

            session.execute(
                audit_table.insert().values(
                    actor_member_id=(principal or {}).get('member_id'),
                    action='role.revoke',
                    target_type='role_assignment',
                    target_id=assignment_id,
                    club_id=row.club_id,
                    metadata={
                        'roleCode': row.role_code,
                        'userId': row.user_id,
                        'scope': row.scope_type,
                        'clubShortName': row.club_short_name or '',
                    },
                )
            )

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return jsonify({'success': True, 'assignmentId': assignment_id})

    return bp
