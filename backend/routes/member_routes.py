from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import Date, Integer, String, and_, cast, func, or_, select
from werkzeug.security import check_password_hash, generate_password_hash


def create_member_blueprint(deps):
    bp = Blueprint('member', __name__)

    get_valid_club_short_names = deps['get_valid_club_short_names']
    log_database_target = deps['log_database_target']
    get_read_db_for_club = deps['get_read_db_for_club']
    get_db_for_club = deps['get_db_for_club']
    get_column = deps['get_column']
    get_identifier_column = deps['get_identifier_column']
    member_to_dict = deps['member_to_dict']
    issue_member_token_pair = deps['issue_member_token_pair']
    load_member_roles = deps['load_member_roles']
    extract_bearer_token = deps['extract_bearer_token']
    revoke_member_session_token = deps['revoke_member_session_token']
    revoke_member_refresh_token = deps['revoke_member_refresh_token']
    get_member_refresh_session_from_token = deps['get_member_refresh_session_from_token']
    require_permission = deps['require_permission']
    require_self_or_permission = deps['require_self_or_permission']
    wildcard_to_sql_like = deps['wildcard_to_sql_like']
    FILTERABLE_COLUMNS = deps['FILTERABLE_COLUMNS']
    is_postgres_writes_enabled = deps['is_postgres_writes_enabled']
    get_postgres_backend = deps['get_postgres_backend']
    _resolve_postgres_club_id = deps['_resolve_postgres_club_id']
    _build_postgres_member_values = deps['_build_postgres_member_values']

    def resolve_user_id_for_member(member_id):
        try:
            member_id_int = int(member_id)
        except (TypeError, ValueError):
            return None

        if not is_postgres_writes_enabled():
            return None

        backend = get_postgres_backend()
        links_table = backend.get('member_user_links_table')
        if links_table is None:
            return None

        session = backend['session_factory']()
        try:
            return session.execute(
                select(links_table.c.user_id).where(links_table.c.member_id == member_id_int)
            ).scalar_one_or_none()
        finally:
            session.close()

    @bp.route('/login', methods=['POST'])
    def login():
        data = request.json or {}
        username = data.get('username')
        password = data.get('password')
        club = data.get('club', 'GAAFFS')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        valid_clubs = get_valid_club_short_names()
        if club not in valid_clubs:
            return jsonify({'error': 'Invalid club selection'}), 400

        log_database_target(club)
        db_info = get_read_db_for_club(club)
        session = db_info['session']
        members_table = db_info['members_table']
        Member = db_info['Member']

        password_column = get_column('password', members_table)
        name_column = get_column('Members_Name', members_table)
        username_column = get_column('username', members_table)
        id_column = get_identifier_column(members_table)

        if password_column is None or id_column is None or (name_column is None and username_column is None):
            return jsonify({'success': False, 'error': 'Login columns are missing from members table'}), 500

        user = None
        if name_column is not None:
            query = select(Member).where(name_column == username)
            user = session.scalars(query).first()
            if user:
                stored_password = getattr(user, password_column.name)
                if check_password_hash(stored_password, password):
                    user_dict = member_to_dict(user, members_table)
                    member_id = user_dict.get(id_column.name)
                    user_id = resolve_user_id_for_member(member_id)
                    token_payload = issue_member_token_pair(member_id, club, username, user_id=user_id)
                    role_payload = load_member_roles(member_id, club, user_id=user_id)
                    user_dict.pop('password', None)
                    return jsonify({
                        'success': True,
                        'userId': user_id,
                        'user': user_dict,
                        'roles': role_payload.get('effective_roles', []),
                        'permissions': role_payload.get('permissions', []),
                        **token_payload,
                    })
                user = None

        if username_column is not None and user is None:
            query = select(Member).where(username_column == username)
            user = session.scalars(query).first()
            if user:
                stored_password = getattr(user, password_column.name)
                if check_password_hash(stored_password, password):
                    user_dict = member_to_dict(user, members_table)
                    member_id = user_dict.get(id_column.name)
                    user_id = resolve_user_id_for_member(member_id)
                    token_payload = issue_member_token_pair(member_id, club, username, user_id=user_id)
                    role_payload = load_member_roles(member_id, club, user_id=user_id)
                    user_dict.pop('password', None)
                    return jsonify({
                        'success': True,
                        'userId': user_id,
                        'user': user_dict,
                        'roles': role_payload.get('effective_roles', []),
                        'permissions': role_payload.get('permissions', []),
                        **token_payload,
                    })

        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

    @bp.route('/logout', methods=['POST'])
    def logout():
        token_value = extract_bearer_token()
        data = request.json or {}
        refresh_token_value = str(data.get('refreshToken', '')).strip()
        if token_value:
            try:
                revoke_member_session_token(token_value)
            except Exception:
                current_app.logger.warning('Failed to revoke member session token during logout', exc_info=True)
        if refresh_token_value:
            try:
                revoke_member_refresh_token(refresh_token_value)
            except Exception:
                current_app.logger.warning('Failed to revoke member refresh token during logout', exc_info=True)
        return jsonify({'success': True})

    @bp.route('/token/refresh', methods=['POST'])
    def refresh_member_token():
        data = request.json or {}
        refresh_token_value = str(data.get('refreshToken', '')).strip()
        if not refresh_token_value:
            return jsonify({'error': 'refreshToken is required'}), 400

        refresh_session = get_member_refresh_session_from_token(refresh_token_value)
        if refresh_session is None:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            revoke_member_refresh_token(refresh_token_value)
        except Exception:
            current_app.logger.warning('Failed to rotate refresh token', exc_info=True)
            return jsonify({'error': 'Failed to refresh session'}), 500

        token_payload = issue_member_token_pair(
            refresh_session.get('member_id'),
            refresh_session.get('club_short_name'),
            refresh_session.get('username'),
            user_id=refresh_session.get('user_id'),
        )
        return jsonify({'success': True, **token_payload})

    @bp.route('/members', methods=['GET'])
    def get_members():
        club = request.args.get('club', 'GAAFFS')
        auth_error = require_permission('member.club.list', club)
        if auth_error:
            return auth_error
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        sort_by = request.args.get('sort_by')
        sort_order = request.args.get('sort_order', 'asc')

        log_database_target(club)
        db_info = get_read_db_for_club(club)
        session = db_info['session']
        members_table = db_info['members_table']
        Member = db_info['Member']

        filters = []
        for column_name in FILTERABLE_COLUMNS:
            raw_filter = request.args.get(column_name)
            if raw_filter is None:
                continue
            filter_value = raw_filter.strip()
            if not filter_value:
                continue
            column = get_column(column_name, members_table)
            if column is None:
                continue
            if filter_value == '[BLANK]':
                filters.append(or_(column.is_(None), cast(column, String) == ''))
            else:
                filters.append(cast(column, String).ilike(wildcard_to_sql_like(filter_value), escape='\\'))

        members_query = select(Member)
        total_query = select(func.count()).select_from(members_table)

        if filters:
            filter_expression = and_(*filters)
            members_query = members_query.where(filter_expression)
            total_query = total_query.where(filter_expression)

        if sort_by:
            sort_column = get_column(sort_by, members_table)
            if sort_column is not None:
                if sort_by in ('Number', 'ID'):
                    sort_expression = cast(sort_column, Integer)
                elif sort_by == 'Licence_Exp':
                    sort_expression = cast(sort_column, Date)
                else:
                    sort_expression = sort_column

                if sort_order == 'desc':
                    members_query = members_query.order_by(sort_expression.desc())
                else:
                    members_query = members_query.order_by(sort_expression.asc())

        members_query = members_query.limit(limit).offset(offset)
        members = session.scalars(members_query).all()
        total = session.execute(total_query).scalar_one()

        members_payload = [member_to_dict(member, members_table) for member in members]
        return jsonify({'members': members_payload, 'total': total})

    @bp.route('/members', methods=['POST'])
    def add_member():
        data = request.json or {}
        club = data.get('club', 'GAAFFS')
        auth_error = require_permission('member.club.create', club)
        if auth_error:
            return auth_error
        log_database_target(club)
        if is_postgres_writes_enabled():
            backend = get_postgres_backend()
            session = backend['session_factory']()
            try:
                club_id = _resolve_postgres_club_id(session, club)
                if club_id is None:
                    return jsonify({'error': 'Invalid club selection'}), 400

                values = _build_postgres_member_values(data)
                defaults = {}
                for required_key in ('members_name', 'number', 'member_type', 'paid_up_2026'):
                    if required_key not in values:
                        defaults[required_key] = ''
                session.execute(backend['members_table'].insert().values(club_id=club_id, **defaults, **values))
                session.commit()
            except Exception as exc:
                session.rollback()
                return jsonify({'error': str(exc)}), 500
            finally:
                session.close()
        else:
            db_info = get_db_for_club(club)
            session = db_info['session']
            members_table = db_info['members_table']
            Member = db_info['Member']

            member = Member()
            for field_name in ('Members_Name', 'Number', 'Member_Type', 'Paid_Up_2026'):
                if get_column(field_name, members_table) is not None:
                    setattr(member, field_name, data.get(field_name))

            session.add(member)
            session.commit()
        return jsonify({'status': 'success'})

    @bp.route('/members/<int:member_id>', methods=['PUT'])
    def update_member(member_id):
        data = request.json or {}
        club = data.get('club', 'GAAFFS')
        auth_error = require_self_or_permission(member_id, 'member.club.update', club)
        if auth_error:
            return auth_error
        log_database_target(club)
        if is_postgres_writes_enabled():
            backend = get_postgres_backend()
            session = backend['session_factory']()
            try:
                club_id = _resolve_postgres_club_id(session, club)
                if club_id is None:
                    return jsonify({'error': 'Invalid club selection'}), 400

                values = _build_postgres_member_values({k: v for k, v in data.items() if k not in {'club', 'ID', 'id'}})
                if not values:
                    return jsonify({'status': 'success'})

                updated = session.execute(
                    backend['members_table'].update().where(
                        and_(backend['members_table'].c.club_id == club_id, backend['members_table'].c.id == member_id)
                    ).values(**values)
                )
                if updated.rowcount == 0:
                    return jsonify({'error': 'Member not found'}), 404
                session.commit()
            except Exception as exc:
                session.rollback()
                return jsonify({'error': str(exc)}), 500
            finally:
                session.close()
        else:
            db_info = get_db_for_club(club)
            session = db_info['session']
            members_table = db_info['members_table']
            Member = db_info['Member']

            id_column = get_column('id', members_table) or get_column('ID', members_table)
            if id_column is None:
                return jsonify({'error': 'No ID column available for update'}), 400

            member = session.scalars(select(Member).where(id_column == member_id)).first()
            if member is None:
                return jsonify({'error': 'Member not found'}), 404

            reserved_fields = {'club', 'ID', 'id'}
            for field_name, field_value in data.items():
                if field_name in reserved_fields:
                    continue
                if get_column(field_name, members_table) is None:
                    continue
                if field_name == 'password' and field_value:
                    if not str(field_value).startswith(('scrypt:', 'pbkdf2:', 'bcrypt:')):
                        field_value = generate_password_hash(str(field_value))
                setattr(member, field_name, field_value)

            session.commit()
        return jsonify({'status': 'success'})

    @bp.route('/members/<int:member_id>', methods=['DELETE'])
    def delete_member(member_id):
        club = request.args.get('club', 'GAAFFS')
        auth_error = require_permission('member.club.delete', club)
        if auth_error:
            return auth_error
        log_database_target(club)
        if is_postgres_writes_enabled():
            backend = get_postgres_backend()
            session = backend['session_factory']()
            try:
                club_id = _resolve_postgres_club_id(session, club)
                if club_id is None:
                    return jsonify({'error': 'Invalid club selection'}), 400
                deleted = session.execute(
                    backend['members_table'].delete().where(
                        and_(backend['members_table'].c.club_id == club_id, backend['members_table'].c.id == member_id)
                    )
                )
                if deleted.rowcount == 0:
                    return jsonify({'error': 'Member not found'}), 404
                session.commit()
            except Exception as exc:
                session.rollback()
                return jsonify({'error': str(exc)}), 500
            finally:
                session.close()
        else:
            db_info = get_db_for_club(club)
            session = db_info['session']
            members_table = db_info['members_table']
            Member = db_info['Member']

            id_column = get_column('id', members_table) or get_column('ID', members_table)
            if id_column is None:
                return jsonify({'error': 'No ID column available for delete'}), 400

            member = session.scalars(select(Member).where(id_column == member_id)).first()
            if member is None:
                return jsonify({'error': 'Member not found'}), 404

            session.delete(member)
            session.commit()
        return jsonify({'status': 'success'})

    @bp.route('/member_by_number/<number>', methods=['GET'])
    def get_member_by_number(number):
        club = request.args.get('club', 'GAAFFS')
        auth_error = require_permission('member.club.list', club)
        if auth_error:
            return auth_error
        log_database_target(club)
        db_info = get_read_db_for_club(club)
        session = db_info['session']
        members_table = db_info['members_table']
        Member = db_info['Member']

        number_column = get_column('Number', members_table)
        if number_column is None:
            return jsonify({'error': 'Number column not found'}), 500

        member = session.scalars(select(Member).where(number_column == number)).first()
        if member is None:
            return jsonify({'error': 'Member not found'}), 404

        return jsonify(member_to_dict(member, members_table))

    return bp
