import csv
import io
from datetime import datetime

from flask import Blueprint, Response, current_app, jsonify, request
from sqlalchemy import Date, Float, Integer, String, and_, case, cast, func, or_, select, text
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
    get_current_principal = deps['get_current_principal']
    require_authenticated = deps['require_authenticated']
    require_permission = deps['require_permission']
    require_self_or_permission = deps['require_self_or_permission']
    wildcard_to_sql_like = deps['wildcard_to_sql_like']
    FILTERABLE_COLUMNS = deps['FILTERABLE_COLUMNS']
    is_postgres_reads_enabled = deps.get('is_postgres_reads_enabled', lambda: False)
    is_postgres_writes_enabled = deps['is_postgres_writes_enabled']
    get_postgres_backend = deps['get_postgres_backend']
    _resolve_postgres_club_id = deps['_resolve_postgres_club_id']
    _build_postgres_member_values = deps['_build_postgres_member_values']

    def try_app_user_login(username, password, club):
        """Try to authenticate against the central app_users table.

        Returns a Flask Response on success or definitive failure.
        Returns None when the username is not found in app_users,
        signalling that the caller should fall through to the per-club
        members-table lookup (transition-period fallback).
        """
        if not is_postgres_reads_enabled():
            return None

        backend = get_postgres_backend()
        app_users_table = backend.get('app_users_table')
        links_table = backend.get('member_user_links_table')
        clubs_table = backend.get('clubs_table')
        if app_users_table is None or links_table is None or clubs_table is None:
            return None

        # Case-insensitive username lookup; skip rows with empty username
        session = backend['session_factory']()
        try:
            au_row = session.execute(
                select(
                    app_users_table.c.id,
                    app_users_table.c.username,
                    app_users_table.c.display_name,
                    app_users_table.c.password_hash,
                    app_users_table.c.is_active,
                ).where(
                    and_(
                        func.lower(app_users_table.c.username) == username.lower(),
                        app_users_table.c.username != '',
                    )
                )
            ).fetchone()
        finally:
            session.close()

        if au_row is None:
            return None  # Not in app_users — fall through to per-club lookup

        # User found; all further responses are definitive (no fall-through)
        if not au_row.is_active:
            return jsonify({'success': False, 'error': 'Account is inactive'}), 401

        if not au_row.password_hash or not check_password_hash(au_row.password_hash, password):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

        # Resolve the member_id for the selected club via member_user_links
        session2 = backend['session_factory']()
        try:
            link_row = session2.execute(
                select(links_table.c.member_id)
                .select_from(
                    links_table.join(clubs_table, links_table.c.club_id == clubs_table.c.id)
                )
                .where(
                    and_(
                        links_table.c.user_id == au_row.id,
                        clubs_table.c.short_name == club,
                    )
                )
            ).fetchone()
        finally:
            session2.close()

        if link_row is None:
            return jsonify({'success': False, 'error': 'Not a member of the selected club'}), 403

        user_id = au_row.id
        member_id = link_row.member_id
        token_payload = issue_member_token_pair(member_id, club, au_row.username, user_id=user_id, user_type="member")
        role_payload = load_member_roles(member_id, club, user_id=user_id)
        return jsonify({
            'success': True,
            'userId': user_id,
            'user': {
                'id': user_id,
                'username': au_row.username,
                'display_name': au_row.display_name,
            },
            'roles': role_payload.get('effective_roles', []),
            'global_roles': role_payload.get('global_roles', []),
            'club_roles': role_payload.get('club_roles', []),
            'permissions': role_payload.get('permissions', []),
            **token_payload,
        })

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

    CATCH_COUNT_FIELDS = (
        'small_trout',
        'medium_trout',
        'large_trout',
        'small_grayling',
        'medium_grayling',
        'large_grayling',
        'other_fish',
    )

    def _parse_non_negative_int(raw_value):
        if raw_value is None or str(raw_value).strip() == '':
            return 0
        try:
            parsed = int(raw_value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None

    def _parse_iso_date(raw_value):
        value = str(raw_value or '').strip()
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None

    def _serialize_catch_return_row(row):
        return {
            'id': row.id,
            'session_date': row.session_date.isoformat() if row.session_date else '',
            'beat_id': row.beat_id or '',
            'small_trout': int(row.small_trout or 0),
            'medium_trout': int(row.medium_trout or 0),
            'large_trout': int(row.large_trout or 0),
            'small_grayling': int(row.small_grayling or 0),
            'medium_grayling': int(row.medium_grayling or 0),
            'large_grayling': int(row.large_grayling or 0),
            'other_fish': int(row.other_fish or 0),
            'flies_used': row.flies_used or '',
            'weather_conditions': row.weather_conditions or '',
            'predator_damage': row.predator_damage or '',
            'created_at': row.created_at.isoformat() if row.created_at else None,
        }

    def _ensure_sqlite_catch_returns_table(session):
        session.execute(text(
            """
            CREATE TABLE IF NOT EXISTS catch_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                beat_id TEXT NOT NULL DEFAULT '',
                small_trout INTEGER NOT NULL DEFAULT 0,
                medium_trout INTEGER NOT NULL DEFAULT 0,
                large_trout INTEGER NOT NULL DEFAULT 0,
                small_grayling INTEGER NOT NULL DEFAULT 0,
                medium_grayling INTEGER NOT NULL DEFAULT 0,
                large_grayling INTEGER NOT NULL DEFAULT 0,
                other_fish INTEGER NOT NULL DEFAULT 0,
                flies_used TEXT NOT NULL DEFAULT '',
                weather_conditions TEXT NOT NULL DEFAULT '',
                predator_damage TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))

    @bp.route('/login', methods=['POST'])
    def login():
        data = request.json or {}
        username = data.get('username')
        password = data.get('password')
        club = data.get('club', 'TEST')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        valid_clubs = get_valid_club_short_names()
        if club not in valid_clubs:
            return jsonify({'error': 'Invalid club selection'}), 400

        # --- Primary: authenticate against central app_users table ---
        app_user_response = try_app_user_login(username, password, club)
        if app_user_response is not None:
            return app_user_response

        # --- Fallback: per-club members table (transition period / empty username) ---
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
                    token_payload = issue_member_token_pair(member_id, club, username, user_id=user_id, user_type="member")
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
                    token_payload = issue_member_token_pair(member_id, club, username, user_id=user_id, user_type="member")
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
            user_type="member",
        )
        return jsonify({'success': True, **token_payload})

    @bp.route('/members', methods=['GET'])
    def get_members():
        club = request.args.get('club', 'TEST')
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
                if sort_by in ('Number', 'ID', 'Age', 'Subs_Expected', 'Subs_paid', 'Join_Fee'):
                    if is_postgres_reads_enabled():
                        normalized_number = func.nullif(func.trim(cast(sort_column, String)), '')
                        numeric_sort_expression = case(
                            (normalized_number.op('~')(r'^-?[0-9]+(?:\.[0-9]+)?$'), cast(normalized_number, Float)),
                            else_=None,
                        )
                        if sort_order == 'desc':
                            members_query = members_query.order_by(
                                numeric_sort_expression.desc().nullslast(),
                                normalized_number.desc().nullslast(),
                            )
                        else:
                            members_query = members_query.order_by(
                                numeric_sort_expression.asc().nullslast(),
                                normalized_number.asc().nullslast(),
                            )
                        sort_expression = None
                    else:
                        sort_expression = cast(sort_column, Float)
                elif sort_by in ('Licence_Exp', 'Date_of_Birth'):
                    sort_expression = cast(sort_column, Date)
                else:
                    sort_expression = sort_column

                if sort_expression is not None:
                    if sort_order == 'desc':
                        members_query = members_query.order_by(sort_expression.desc())
                    else:
                        members_query = members_query.order_by(sort_expression.asc())

        members_query = members_query.limit(limit).offset(offset)
        members = session.scalars(members_query).all()
        total = session.execute(total_query).scalar_one()

        members_payload = [member_to_dict(member, members_table) for member in members]
        return jsonify({'members': members_payload, 'total': total})

    @bp.route('/members/export', methods=['GET'])
    def export_members():
        club = request.args.get('club', 'TEST')
        auth_error = require_permission('member.club.list', club)
        if auth_error:
            return auth_error

        export_format = str(request.args.get('format', 'csv')).strip().lower()
        if export_format not in ('csv', 'json'):
            return jsonify({'error': 'format must be csv or json'}), 400

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

        if filters:
            members_query = members_query.where(and_(*filters))

        if sort_by:
            sort_column = get_column(sort_by, members_table)
            if sort_column is not None:
                if sort_by in ('Number', 'ID', 'Age', 'Subs_Expected', 'Subs_paid', 'Join_Fee'):
                    if is_postgres_reads_enabled():
                        normalized_number = func.nullif(func.trim(cast(sort_column, String)), '')
                        numeric_sort_expression = case(
                            (normalized_number.op('~')(r'^-?[0-9]+(?:\.[0-9]+)?$'), cast(normalized_number, Float)),
                            else_=None,
                        )
                        if sort_order == 'desc':
                            members_query = members_query.order_by(
                                numeric_sort_expression.desc().nullslast(),
                                normalized_number.desc().nullslast(),
                            )
                        else:
                            members_query = members_query.order_by(
                                numeric_sort_expression.asc().nullslast(),
                                normalized_number.asc().nullslast(),
                            )
                        sort_expression = None
                    else:
                        sort_expression = cast(sort_column, Float)
                elif sort_by in ('Licence_Exp', 'Date_of_Birth'):
                    sort_expression = cast(sort_column, Date)
                else:
                    sort_expression = sort_column

                if sort_expression is not None:
                    if sort_order == 'desc':
                        members_query = members_query.order_by(sort_expression.desc())
                    else:
                        members_query = members_query.order_by(sort_expression.asc())

        members = session.scalars(members_query).all()
        members_payload = [member_to_dict(member, members_table) for member in members]
        for row in members_payload:
            row.pop('password', None)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        if export_format == 'json':
            response_body = {
                'club': club,
                'total': len(members_payload),
                'members': members_payload,
            }
            response = jsonify(response_body)
            response.headers['Content-Disposition'] = f'attachment; filename="{club}_members_{timestamp}.json"'
            return response

        csv_buffer = io.StringIO()
        if members_payload:
            fieldnames = list(members_payload[0].keys())
        else:
            fieldnames = [name for name in members_table.c.keys() if str(name).lower() != 'password']

        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(members_payload)

        return Response(
            csv_buffer.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={
                'Content-Disposition': f'attachment; filename="{club}_members_{timestamp}.csv"',
            },
        )

    @bp.route('/members/me', methods=['GET'])
    def get_current_member_profile():
        requested_club = str(request.args.get('club', '')).strip()
        auth_error = require_authenticated(requested_club)
        if auth_error:
            return auth_error

        principal = get_current_principal(requested_club)
        if principal is None:
            return jsonify({'error': 'Unauthorized'}), 401

        member_id = principal.get('member_id')
        club = str(principal.get('scope_club_short_name') or principal.get('club_short_name') or '').strip()
        if not member_id or not club:
            return jsonify({'error': 'Member session is missing identity details'}), 400

        log_database_target(club)
        db_info = get_read_db_for_club(club)
        session = db_info['session']
        members_table = db_info['members_table']
        Member = db_info['Member']

        id_column = get_column('id', members_table)
        if id_column is None:
            id_column = get_column('ID', members_table)
        if id_column is None:
            return jsonify({'error': 'No ID column available for lookup'}), 500

        member = session.scalars(select(Member).where(id_column == member_id)).first()
        if member is None:
            return jsonify({'error': 'Member not found'}), 404

        member_payload = member_to_dict(member, members_table)
        member_payload.pop('password', None)
        return jsonify({'member': member_payload, 'club': club})

    @bp.route('/catch-returns', methods=['POST'])
    def create_catch_return():
        data = request.json or {}
        requested_club = str(data.get('club', '')).strip()
        auth_error = require_authenticated(requested_club)
        if auth_error:
            return auth_error

        principal = get_current_principal(requested_club)
        if principal is None:
            return jsonify({'error': 'Unauthorized'}), 401

        member_id = principal.get('member_id')
        club = str(principal.get('scope_club_short_name') or principal.get('club_short_name') or '').strip()
        if not member_id or not club:
            return jsonify({'error': 'Member session is missing identity details'}), 400

        session_date = _parse_iso_date(data.get('date') or data.get('session_date'))
        if session_date is None:
            return jsonify({'error': 'Date is required and must be YYYY-MM-DD'}), 400

        beat_id = str(data.get('beat_id', '')).strip()
        if not beat_id:
            return jsonify({'error': 'Beat ID is required'}), 400

        counts = {}
        for field_name in CATCH_COUNT_FIELDS:
            parsed_value = _parse_non_negative_int(data.get(field_name, 0))
            if parsed_value is None:
                return jsonify({'error': f'{field_name} must be a non-negative whole number'}), 400
            counts[field_name] = parsed_value

        flies_used = str(data.get('flies_used', '')).strip()
        weather_conditions = str(data.get('weather_conditions', '')).strip()
        predator_damage = str(data.get('predator_damage', '')).strip()

        if is_postgres_writes_enabled():
            backend = get_postgres_backend()
            catch_returns_table = backend.get('catch_returns_table')
            if catch_returns_table is None:
                return jsonify({'error': 'Catch return table is unavailable'}), 500

            session = backend['session_factory']()
            try:
                club_id = _resolve_postgres_club_id(session, club)
                if club_id is None:
                    return jsonify({'error': 'Invalid club selection'}), 400

                insert_result = session.execute(
                    catch_returns_table.insert().values(
                        club_id=club_id,
                        member_id=int(member_id),
                        session_date=session_date,
                        beat_id=beat_id,
                        flies_used=flies_used,
                        weather_conditions=weather_conditions,
                        predator_damage=predator_damage,
                        **counts,
                    ).returning(catch_returns_table.c.id)
                )
                new_id = insert_result.scalar_one()
                session.commit()
                return jsonify({'status': 'success', 'id': int(new_id), 'club': club}), 201
            except Exception as exc:
                session.rollback()
                return jsonify({'error': str(exc)}), 500
            finally:
                session.close()

        db_info = get_db_for_club(club)
        session = db_info['session']
        try:
            _ensure_sqlite_catch_returns_table(session)
            session.execute(
                text(
                    """
                    INSERT INTO catch_returns (
                        member_id,
                        session_date,
                        beat_id,
                        small_trout,
                        medium_trout,
                        large_trout,
                        small_grayling,
                        medium_grayling,
                        large_grayling,
                        other_fish,
                        flies_used,
                        weather_conditions,
                        predator_damage,
                        created_at,
                        updated_at
                    ) VALUES (
                        :member_id,
                        :session_date,
                        :beat_id,
                        :small_trout,
                        :medium_trout,
                        :large_trout,
                        :small_grayling,
                        :medium_grayling,
                        :large_grayling,
                        :other_fish,
                        :flies_used,
                        :weather_conditions,
                        :predator_damage,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP
                    )
                    """
                ),
                {
                    'member_id': int(member_id),
                    'session_date': session_date.isoformat(),
                    'beat_id': beat_id,
                    'small_trout': counts['small_trout'],
                    'medium_trout': counts['medium_trout'],
                    'large_trout': counts['large_trout'],
                    'small_grayling': counts['small_grayling'],
                    'medium_grayling': counts['medium_grayling'],
                    'large_grayling': counts['large_grayling'],
                    'other_fish': counts['other_fish'],
                    'flies_used': flies_used,
                    'weather_conditions': weather_conditions,
                    'predator_damage': predator_damage,
                }
            )
            session.commit()
            return jsonify({'status': 'success', 'club': club}), 201
        except Exception as exc:
            session.rollback()
            return jsonify({'error': str(exc)}), 500

    @bp.route('/catch-returns/mine', methods=['GET'])
    def list_my_catch_returns():
        requested_club = str(request.args.get('club', '')).strip()
        auth_error = require_authenticated(requested_club)
        if auth_error:
            return auth_error

        principal = get_current_principal(requested_club)
        if principal is None:
            return jsonify({'error': 'Unauthorized'}), 401

        member_id = principal.get('member_id')
        club = str(principal.get('scope_club_short_name') or principal.get('club_short_name') or '').strip()
        if not member_id or not club:
            return jsonify({'error': 'Member session is missing identity details'}), 400

        limit = request.args.get('limit', default=50, type=int)
        if not limit or limit < 1:
            limit = 50
        limit = min(limit, 200)

        if is_postgres_reads_enabled():
            backend = get_postgres_backend()
            catch_returns_table = backend.get('catch_returns_table')
            if catch_returns_table is None:
                return jsonify({'returns': [], 'club': club})

            session = backend['session_factory']()
            try:
                club_id = _resolve_postgres_club_id(session, club)
                if club_id is None:
                    return jsonify({'returns': [], 'club': club})

                rows = session.execute(
                    select(catch_returns_table)
                    .where(
                        and_(
                            catch_returns_table.c.club_id == club_id,
                            catch_returns_table.c.member_id == int(member_id),
                        )
                    )
                    .order_by(catch_returns_table.c.session_date.desc(), catch_returns_table.c.created_at.desc())
                    .limit(limit)
                ).fetchall()
                payload = [_serialize_catch_return_row(row) for row in rows]
                return jsonify({'returns': payload, 'club': club})
            finally:
                session.close()

        db_info = get_read_db_for_club(club)
        session = db_info['session']
        try:
            _ensure_sqlite_catch_returns_table(session)
            rows = session.execute(
                text(
                    """
                    SELECT
                        id,
                        session_date,
                        beat_id,
                        small_trout,
                        medium_trout,
                        large_trout,
                        small_grayling,
                        medium_grayling,
                        large_grayling,
                        other_fish,
                        flies_used,
                        weather_conditions,
                        predator_damage,
                        created_at
                    FROM catch_returns
                    WHERE member_id = :member_id
                    ORDER BY session_date DESC, created_at DESC
                    LIMIT :limit
                    """
                ),
                {'member_id': int(member_id), 'limit': limit}
            ).fetchall()
            payload = [
                {
                    'id': int(row.id),
                    'session_date': str(row.session_date or ''),
                    'beat_id': str(row.beat_id or ''),
                    'small_trout': int(row.small_trout or 0),
                    'medium_trout': int(row.medium_trout or 0),
                    'large_trout': int(row.large_trout or 0),
                    'small_grayling': int(row.small_grayling or 0),
                    'medium_grayling': int(row.medium_grayling or 0),
                    'large_grayling': int(row.large_grayling or 0),
                    'other_fish': int(row.other_fish or 0),
                    'flies_used': str(row.flies_used or ''),
                    'weather_conditions': str(row.weather_conditions or ''),
                    'predator_damage': str(row.predator_damage or ''),
                    'created_at': str(row.created_at or ''),
                }
                for row in rows
            ]
            return jsonify({'returns': payload, 'club': club})
        finally:
            session.close()

    @bp.route('/members', methods=['POST'])
    def add_member():
        data = request.json or {}
        club = data.get('club', 'TEST')
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
        club = data.get('club', 'TEST')
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

            id_column = get_column('id', members_table)
            if id_column is None:
                id_column = get_column('ID', members_table)
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
        club = request.args.get('club', 'TEST')
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

            id_column = get_column('id', members_table)
            if id_column is None:
                id_column = get_column('ID', members_table)
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
        club = request.args.get('club', 'TEST')
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
