import re
import smtplib

from email.message import EmailMessage
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import String, and_, cast, select


def create_newsletter_blueprint(deps):
    bp = Blueprint('newsletter', __name__)

    require_member_token_for_club = deps['require_member_token_for_club']
    get_valid_club_short_names = deps['get_valid_club_short_names']
    log_database_target = deps['log_database_target']
    get_read_db_for_club = deps['get_read_db_for_club']
    get_db_for_club = deps['get_db_for_club']
    get_postgres_backend = deps['get_postgres_backend']
    _resolve_postgres_club_id = deps['_resolve_postgres_club_id']
    is_postgres_writes_enabled = deps['is_postgres_writes_enabled']
    get_column = deps['get_column']
    get_identifier_column = deps['get_identifier_column']
    build_member_filters = deps['build_member_filters']
    member_to_dict = deps['member_to_dict']
    normalize_newsletter_filters = deps['normalize_newsletter_filters']
    render_newsletter_template = deps['render_newsletter_template']
    NEWSLETTER_TEMPLATES = deps['NEWSLETTER_TEMPLATES']
    NEWSLETTER_TEMPLATE_TAGS = deps['NEWSLETTER_TEMPLATE_TAGS']
    get_smtp_config_for_club = deps['get_smtp_config_for_club']

    @bp.route('/newsletter/prepare_recipients', methods=['POST'])
    def prepare_newsletter_recipients():
        data = request.json or {}
        club = data.get('club', 'GAAFFS')
        auth_error = require_member_token_for_club(club)
        if auth_error:
            return auth_error
        member_ids = data.get('memberIds', [])

        if not isinstance(member_ids, list) or not member_ids:
            return jsonify({'error': 'memberIds must be a non-empty list'}), 400

        valid_clubs = get_valid_club_short_names()
        if club not in valid_clubs:
            return jsonify({'error': 'Invalid club selection'}), 400

        selected_ids = {str(member_id).strip() for member_id in member_ids if str(member_id).strip()}
        if not selected_ids:
            return jsonify({'error': 'No valid member IDs supplied'}), 400

        log_database_target(club)
        db_info = get_read_db_for_club(club)
        session = db_info['session']
        members_table = db_info['members_table']
        Member = db_info['Member']

        id_column = get_column('id', members_table) or get_column('ID', members_table) or get_column('Number', members_table)
        if id_column is None:
            return jsonify({'error': 'No identifier column available in members table'}), 500

        matched_members = session.scalars(select(Member).where(cast(id_column, String).in_(list(selected_ids)))).all()

        email_column = get_column('E_Mail', members_table) or get_column('email', members_table)
        name_column = get_column('Members_Name', members_table) or get_column('name', members_table)
        number_column = get_column('Number', members_table)
        member_type_column = get_column('Member_Type', members_table)
        paid_up_column = get_column('Paid_Up_2026', members_table)

        recipients = []
        missing_email_count = 0
        for member in matched_members:
            member_payload = member_to_dict(member, members_table)
            email_value = str(member_payload.get(email_column.name, '')).strip() if email_column is not None else ''
            if not email_value:
                missing_email_count += 1
                continue

            recipients.append({
                'memberId': member_payload.get(id_column.name),
                'Number': member_payload.get(number_column.name) if number_column is not None else '',
                'Members_Name': member_payload.get(name_column.name) if name_column is not None else '',
                'E_Mail': email_value,
                'Member_Type': member_payload.get(member_type_column.name) if member_type_column is not None else '',
                'Paid_Up_2026': member_payload.get(paid_up_column.name) if paid_up_column is not None else '',
            })

        return jsonify({
            'club': club,
            'selectedCount': len(selected_ids),
            'matchedCount': len(matched_members),
            'emailableCount': len(recipients),
            'missingEmailCount': missing_email_count,
            'emailWorkflowStatus': 'prepared_not_sent',
            'recipients': recipients,
        })

    @bp.route('/newsletter/templates', methods=['GET'])
    def get_newsletter_templates():
        club = request.args.get('club', 'GAAFFS')
        auth_error = require_member_token_for_club(club)
        if auth_error:
            return auth_error

        sample_context = {
            'Club': club,
            'Title': 'Mr',
            'First_Name': 'John',
            'Last_Name': 'Smith',
            'Preferred_Name': 'John',
            'Members_Name': 'John Smith',
            'Number': '42',
            'Member_Type': 'Standard',
            'E_Mail': 'john.smith@example.com',
        }

        try:
            db_info = get_read_db_for_club(club)
            session = db_info['session']
            newsletter_templates_table = db_info['newsletter_templates_table']
            rows = session.execute(select(newsletter_templates_table)).fetchall()
            session.close()

            templates = []
            for row in rows:
                templates.append({
                    'id': row.id,
                    'name': row.name,
                    'subjectTemplate': row.subject,
                    'bodyTemplate': row.body,
                    'previewSubject': render_newsletter_template(row.subject, sample_context),
                    'previewBody': render_newsletter_template(row.body, sample_context),
                })
        except Exception as exc:
            current_app.logger.warning(f'Error loading newsletter templates from database: {exc}, using defaults')
            templates = [
                {
                    'id': template['id'],
                    'name': template['name'],
                    'subjectTemplate': template['subject'],
                    'bodyTemplate': template['body'],
                    'previewSubject': render_newsletter_template(template['subject'], sample_context),
                    'previewBody': render_newsletter_template(template['body'], sample_context),
                }
                for template in NEWSLETTER_TEMPLATES.values()
            ]

        smtp_cfg = get_smtp_config_for_club(club)
        return jsonify({
            'templates': templates,
            'availableTags': NEWSLETTER_TEMPLATE_TAGS,
            'smtpFromEmail': smtp_cfg.get('fromEmail', ''),
            'smtpFromName': smtp_cfg.get('fromName', ''),
        })

    @bp.route('/newsletter/templates/<template_id>', methods=['PUT'])
    def update_newsletter_template(template_id):
        data = request.json or {}
        club = data.get('club', 'GAAFFS')
        auth_error = require_member_token_for_club(club)
        if auth_error:
            return auth_error
        name = data.get('name', '').strip()
        subject = data.get('subject', '').strip()
        body = data.get('body', '').strip()

        if not name or not subject or not body:
            return jsonify({'error': 'Template name, subject, and body are required'}), 400

        try:
            if is_postgres_writes_enabled():
                backend = get_postgres_backend()
                session = backend['session_factory']()
                club_id = _resolve_postgres_club_id(session, club)
                if club_id is None:
                    return jsonify({'error': 'Invalid club selection'}), 400
                result = session.execute(
                    backend['newsletter_templates_table'].update().where(
                        and_(
                            backend['newsletter_templates_table'].c.club_id == club_id,
                            backend['newsletter_templates_table'].c.template_key == template_id,
                        )
                    ).values(name=name, subject=subject, body=body)
                )
                session.commit()
                session.close()
            else:
                db_info = get_db_for_club(club)
                session = db_info['session']
                newsletter_templates_table = db_info['newsletter_templates_table']
                result = session.execute(
                    newsletter_templates_table.update().where(
                        newsletter_templates_table.c.id == template_id
                    ).values(name=name, subject=subject, body=body)
                )
                session.commit()
                session.close()

            if result.rowcount == 0:
                return jsonify({'error': 'Template not found'}), 404

            return jsonify({'message': 'Template updated successfully', 'id': template_id}), 200
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    @bp.route('/newsletter/templates/<template_id>', methods=['DELETE'])
    def delete_newsletter_template(template_id):
        club = request.args.get('club', 'GAAFFS')
        auth_error = require_member_token_for_club(club)
        if auth_error:
            return auth_error

        if template_id in ('club-update', 'membership-reminder'):
            return jsonify({'error': 'Cannot delete default templates'}), 400

        try:
            if is_postgres_writes_enabled():
                backend = get_postgres_backend()
                session = backend['session_factory']()
                club_id = _resolve_postgres_club_id(session, club)
                if club_id is None:
                    return jsonify({'error': 'Invalid club selection'}), 400
                result = session.execute(
                    backend['newsletter_templates_table'].delete().where(
                        and_(
                            backend['newsletter_templates_table'].c.club_id == club_id,
                            backend['newsletter_templates_table'].c.template_key == template_id,
                        )
                    )
                )
                session.commit()
                session.close()
            else:
                db_info = get_db_for_club(club)
                session = db_info['session']
                newsletter_templates_table = db_info['newsletter_templates_table']
                result = session.execute(
                    newsletter_templates_table.delete().where(newsletter_templates_table.c.id == template_id)
                )
                session.commit()
                session.close()

            if result.rowcount == 0:
                return jsonify({'error': 'Template not found'}), 404

            return jsonify({'message': 'Template deleted successfully'}), 200
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    @bp.route('/newsletter/templates', methods=['POST'])
    def create_newsletter_template():
        data = request.json or {}
        club = data.get('club', 'GAAFFS')
        auth_error = require_member_token_for_club(club)
        if auth_error:
            return auth_error
        template_id = data.get('id', '').strip()
        name = data.get('name', '').strip()
        subject = data.get('subject', '').strip()
        body = data.get('body', '').strip()

        if not template_id or not name or not subject or not body:
            return jsonify({'error': 'Template id, name, subject, and body are required'}), 400

        if not re.match(r'^[a-z0-9\-]+$', template_id):
            return jsonify({'error': 'Template id must contain only lowercase letters, numbers, and hyphens'}), 400

        try:
            if is_postgres_writes_enabled():
                backend = get_postgres_backend()
                session = backend['session_factory']()
                club_id = _resolve_postgres_club_id(session, club)
                if club_id is None:
                    return jsonify({'error': 'Invalid club selection'}), 400
                session.execute(
                    backend['newsletter_templates_table'].insert().values(
                        club_id=club_id,
                        template_key=template_id,
                        name=name,
                        subject=subject,
                        body=body,
                    )
                )
                session.commit()
                session.close()
            else:
                db_info = get_db_for_club(club)
                session = db_info['session']
                newsletter_templates_table = db_info['newsletter_templates_table']
                session.execute(
                    newsletter_templates_table.insert().values(id=template_id, name=name, subject=subject, body=body)
                )
                session.commit()
                session.close()

            return jsonify({'message': 'Template created successfully', 'id': template_id}), 201
        except Exception as exc:
            if 'UNIQUE constraint failed' in str(exc) or 'already exists' in str(exc):
                return jsonify({'error': 'Template id already exists'}), 409
            return jsonify({'error': str(exc)}), 500

    @bp.route('/newsletter/filtered_member_ids', methods=['POST'])
    def get_newsletter_filtered_member_ids():
        data = request.json or {}
        club = data.get('club', 'GAAFFS')
        auth_error = require_member_token_for_club(club)
        if auth_error:
            return auth_error
        filters_source = data.get('filters', {})

        valid_clubs = get_valid_club_short_names()
        if club not in valid_clubs:
            return jsonify({'error': 'Invalid club selection'}), 400

        normalized_filters = normalize_newsletter_filters(filters_source)

        log_database_target(club)
        db_info = get_read_db_for_club(club)
        session = db_info['session']
        members_table = db_info['members_table']
        Member = db_info['Member']

        id_column = get_identifier_column(members_table)
        if id_column is None:
            return jsonify({'error': 'No identifier column available in members table'}), 500

        filters = build_member_filters(members_table, normalized_filters)
        query = select(Member)
        if filters:
            query = query.where(and_(*filters))

        matched_members = session.scalars(query).all()

        member_ids = []
        for member in matched_members:
            member_payload = member_to_dict(member, members_table)
            member_id = member_payload.get(id_column.name)
            if member_id is None:
                continue
            member_id_string = str(member_id).strip()
            if member_id_string:
                member_ids.append(member_id_string)

        return jsonify({'club': club, 'matchedCount': len(member_ids), 'memberIds': member_ids})

    @bp.route('/newsletter/send', methods=['POST'])
    def send_newsletter():
        data = request.json or {}
        club = data.get('club', 'GAAFFS')
        auth_error = require_member_token_for_club(club)
        if auth_error:
            return auth_error
        template_id = str(data.get('templateId', '')).strip()
        scope = str(data.get('scope', 'all_club')).strip().lower()
        member_ids = data.get('memberIds', [])
        filters_source = data.get('filters', {})

        valid_clubs = get_valid_club_short_names()
        if club not in valid_clubs:
            return jsonify({'error': 'Invalid club selection'}), 400

        template = None
        try:
            db_info_tmpl = get_read_db_for_club(club)
            sess_tmpl = db_info_tmpl['session']
            nl_tbl = db_info_tmpl['newsletter_templates_table']
            row = sess_tmpl.execute(select(nl_tbl).where(nl_tbl.c.id == template_id)).fetchone()
            sess_tmpl.close()
            if row:
                template = {'id': row.id, 'name': row.name, 'subject': row.subject, 'body': row.body}
        except Exception as tmpl_exc:
            current_app.logger.warning(f'Could not load template from DB: {tmpl_exc}')
        if template is None:
            template = NEWSLETTER_TEMPLATES.get(template_id)
        if template is None:
            return jsonify({'error': 'Invalid newsletter template selection'}), 400

        smtp_cfg = get_smtp_config_for_club(club)
        smtp_host = smtp_cfg['host']
        smtp_port = smtp_cfg['port']
        smtp_username = smtp_cfg['username']
        smtp_password = smtp_cfg['password']
        smtp_from_email = smtp_cfg['fromEmail']
        smtp_from_name = smtp_cfg['fromName']
        smtp_use_ssl = smtp_cfg['useSsl']
        smtp_use_tls = smtp_cfg['useTls']

        if not smtp_host or not smtp_from_email:
            return jsonify({'error': f'SMTP is not configured for club {club}. Set host and fromEmail in the club SMTP settings or via environment variables.'}), 503

        log_database_target(club)
        db_info = get_read_db_for_club(club)
        session = db_info['session']
        members_table = db_info['members_table']
        Member = db_info['Member']

        id_column = get_identifier_column(members_table)
        if id_column is None:
            return jsonify({'error': 'No identifier column available in members table'}), 500

        members_query = select(Member)
        selected_count = 0

        if scope == 'selected':
            if not isinstance(member_ids, list) or not member_ids:
                return jsonify({'error': 'memberIds must be a non-empty list when scope=selected'}), 400
            selected_ids = {str(member_id).strip() for member_id in member_ids if str(member_id).strip()}
            if not selected_ids:
                return jsonify({'error': 'No valid member IDs supplied'}), 400
            selected_count = len(selected_ids)
            members_query = members_query.where(cast(id_column, String).in_(list(selected_ids)))
        elif scope == 'all_filtered':
            normalized_filters = normalize_newsletter_filters(filters_source)
            filter_clauses = build_member_filters(members_table, normalized_filters)
            if filter_clauses:
                members_query = members_query.where(and_(*filter_clauses))
        elif scope != 'all_club':
            return jsonify({'error': 'Invalid scope. Expected one of: selected, all_filtered, all_club'}), 400

        matched_members = session.scalars(members_query).all()

        email_column = get_column('E_Mail', members_table) or get_column('email', members_table)
        name_column = get_column('Members_Name', members_table) or get_column('name', members_table)
        number_column = get_column('Number', members_table)

        recipients = []
        missing_email_count = 0

        tag_column_map = {}
        for tag_info in NEWSLETTER_TEMPLATE_TAGS:
            if tag_info['source'] == 'column':
                col = get_column(tag_info['tag'], members_table)
                if col is not None:
                    tag_column_map[tag_info['tag']] = col

        for member in matched_members:
            member_payload = member_to_dict(member, members_table)
            email_value = str(member_payload.get(email_column.name, '')).strip() if email_column is not None else ''
            if not email_value:
                missing_email_count += 1
                continue

            member_context = {'Club': club}
            for tag, col in tag_column_map.items():
                member_context[tag] = str(member_payload.get(col.name, '') or '').strip()

            recipients.append({
                'memberId': str(member_payload.get(id_column.name, '')).strip(),
                'context': member_context,
                'email': email_value,
            })

        if not recipients:
            return jsonify({'error': 'No emailable recipients matched the selected scope'}), 400

        sent_count = 0
        failed_deliveries = []

        try:
            if smtp_use_ssl:
                smtp_client = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20)
            else:
                smtp_client = smtplib.SMTP(smtp_host, smtp_port, timeout=20)

            with smtp_client as server:
                if not smtp_use_ssl and smtp_use_tls:
                    server.starttls()
                if smtp_username:
                    server.login(smtp_username, smtp_password)

                for recipient in recipients:
                    render_ctx = recipient['context']
                    subject = render_newsletter_template(template['subject'], render_ctx)
                    body = render_newsletter_template(template['body'], render_ctx)

                    message = EmailMessage()
                    message['Subject'] = subject
                    message['From'] = f'{smtp_from_name} <{smtp_from_email}>'
                    message['To'] = recipient['email']
                    message.set_content(body)

                    try:
                        server.send_message(message)
                        sent_count += 1
                    except Exception as exc:
                        failed_deliveries.append({'email': recipient['email'], 'error': str(exc)})
        except Exception as exc:
            return jsonify({'error': f'Failed to connect or authenticate with SMTP server: {exc}'}), 502

        return jsonify({
            'club': club,
            'templateId': template_id,
            'scope': scope,
            'selectedCount': selected_count,
            'matchedCount': len(matched_members),
            'emailableCount': len(recipients),
            'missingEmailCount': missing_email_count,
            'sentCount': sent_count,
            'failedCount': len(failed_deliveries),
            'failedDeliveries': failed_deliveries,
            'emailWorkflowStatus': 'sent',
        })

    return bp
