import os
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import and_, bindparam, func, select, update
from werkzeug.utils import secure_filename

ALLOWED_DOCUMENT_EXTENSIONS = {
    '.pdf', '.xls', '.xlsx', '.doc', '.docx'
}
MAX_DOCUMENT_SIZE_BYTES = 20 * 1024 * 1024


def create_document_blueprint(deps):
    bp = Blueprint('documents', __name__)

    require_authenticated = deps['require_authenticated']
    require_permission = deps['require_permission']
    get_postgres_backend = deps['get_postgres_backend']
    _resolve_postgres_club_id = deps['_resolve_postgres_club_id']
    get_current_principal = deps['get_current_principal']

    def _resolve_club_from_request(default='TEST'):
        club = (
            request.args.get('club')
            or request.form.get('club')
            or (request.json or {}).get('club')
            or default
        )
        return str(club or '').strip()

    def _fetch_ordered_document_ids(session, table, club_id):
        rows = session.execute(
            select(table.c.id)
            .where(table.c.club_id == club_id)
            .order_by(table.c.display_order.asc(), table.c.id.asc())
        ).fetchall()
        return [int(row.id) for row in rows]

    def _rewrite_display_order(session, table, ordered_ids):
        if not ordered_ids:
            return
        session.execute(
            update(table)
            .where(table.c.id == bindparam('id_param'))
            .values(display_order=bindparam('display_order_param')),
            [
                {
                    'id_param': int(document_id),
                    'display_order_param': index + 1,
                }
                for index, document_id in enumerate(ordered_ids)
            ],
        )

    @bp.route('/documents', methods=['GET'])
    def list_documents():
        club = _resolve_club_from_request()
        auth_error = require_authenticated(club)
        if auth_error:
            return auth_error

        backend = get_postgres_backend()
        session = backend['session_factory']()
        table = backend['club_documents_table']

        try:
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400

            rows = session.execute(
                select(table)
                .where(table.c.club_id == club_id)
                .order_by(table.c.display_order.asc(), table.c.id.asc())
            ).fetchall()

            documents = [
                {
                    'id': row.id,
                    'displayOrder': int(row.display_order or 0),
                    'title': row.title,
                    'fileName': row.file_name,
                    'fileExt': row.file_ext,
                    'mimeType': row.mime_type,
                    'fileSize': int(row.file_size or 0),
                    'uploadedByUserId': row.uploaded_by_user_id,
                    'createdAt': row.created_at.isoformat() if row.created_at else '',
                    'updatedAt': row.updated_at.isoformat() if row.updated_at else '',
                }
                for row in rows
            ]
            return jsonify({'club': club, 'documents': documents})
        finally:
            session.close()

    @bp.route('/documents/<int:document_id>/download', methods=['GET'])
    def download_document(document_id):
        club = _resolve_club_from_request()
        auth_error = require_authenticated(club)
        if auth_error:
            return auth_error

        backend = get_postgres_backend()
        session = backend['session_factory']()
        table = backend['club_documents_table']

        try:
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400

            row = session.execute(
                select(table).where(and_(table.c.id == document_id, table.c.club_id == club_id))
            ).first()
            if row is None:
                return jsonify({'error': 'Document not found'}), 404

            return send_file(
                BytesIO(row.file_data),
                mimetype=row.mime_type or 'application/octet-stream',
                as_attachment=True,
                download_name=row.file_name or f'document-{document_id}',
            )
        finally:
            session.close()

    @bp.route('/documents', methods=['POST'])
    def upload_document():
        club = _resolve_club_from_request()
        auth_error = require_permission('document.club.manage', club)
        if auth_error:
            return auth_error

        upload = request.files.get('file')
        if upload is None or not str(upload.filename or '').strip():
            return jsonify({'error': 'A file is required'}), 400

        safe_filename = secure_filename(upload.filename)
        file_ext = os.path.splitext(safe_filename)[1].lower()
        if file_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            return jsonify({'error': 'Unsupported file type. Allowed: PDF, XLS, XLSX, DOC, DOCX'}), 400

        file_data = upload.read() or b''
        if not file_data:
            return jsonify({'error': 'Uploaded file is empty'}), 400
        if len(file_data) > MAX_DOCUMENT_SIZE_BYTES:
            return jsonify({'error': 'File exceeds 20MB upload limit'}), 413

        title = str(request.form.get('title', '')).strip()
        if not title:
            title = os.path.splitext(safe_filename)[0]

        mime_type = str(upload.mimetype or 'application/octet-stream').strip() or 'application/octet-stream'

        backend = get_postgres_backend()
        session = backend['session_factory']()
        table = backend['club_documents_table']

        try:
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400

            principal = get_current_principal(club) or {}
            uploaded_by_user_id = principal.get('user_id')
            max_display_order = session.execute(
                select(func.max(table.c.display_order)).where(table.c.club_id == club_id)
            ).scalar()
            next_display_order = int(max_display_order or 0) + 1

            insert_result = session.execute(
                table.insert().values(
                    club_id=club_id,
                    display_order=next_display_order,
                    title=title,
                    file_name=safe_filename,
                    file_ext=file_ext,
                    mime_type=mime_type,
                    file_size=len(file_data),
                    file_data=file_data,
                    uploaded_by_user_id=uploaded_by_user_id,
                ).returning(table.c.id, table.c.created_at)
            ).first()
            session.commit()

            return jsonify({
                'message': 'Document uploaded',
                'id': insert_result.id,
                'createdAt': insert_result.created_at.isoformat() if insert_result and insert_result.created_at else '',
            }), 201
        finally:
            session.close()

    @bp.route('/documents/<int:document_id>', methods=['DELETE'])
    def delete_document(document_id):
        club = _resolve_club_from_request()
        auth_error = require_permission('document.club.manage', club)
        if auth_error:
            return auth_error

        backend = get_postgres_backend()
        session = backend['session_factory']()
        table = backend['club_documents_table']

        try:
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400

            result = session.execute(
                table.delete().where(and_(table.c.id == document_id, table.c.club_id == club_id))
            )

            if result.rowcount:
                ordered_ids = _fetch_ordered_document_ids(session, table, club_id)
                _rewrite_display_order(session, table, ordered_ids)
            session.commit()

            if result.rowcount == 0:
                return jsonify({'error': 'Document not found'}), 404
            return jsonify({'message': 'Document deleted'})
        finally:
            session.close()

    @bp.route('/documents/<int:document_id>/order', methods=['PUT'])
    def update_document_order(document_id):
        club = _resolve_club_from_request()
        auth_error = require_permission('document.club.manage', club)
        if auth_error:
            return auth_error

        payload = request.get_json(silent=True) or {}
        raw_display_order = (
            payload.get('displayOrder')
            or payload.get('display_order')
            or request.form.get('displayOrder')
            or request.form.get('display_order')
            or request.args.get('displayOrder')
            or request.args.get('display_order')
        )

        try:
            requested_order = int(raw_display_order)
        except (TypeError, ValueError):
            return jsonify({'error': 'displayOrder must be a positive integer'}), 400

        if requested_order < 1:
            return jsonify({'error': 'displayOrder must be a positive integer'}), 400

        backend = get_postgres_backend()
        session = backend['session_factory']()
        table = backend['club_documents_table']

        try:
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400

            existing = session.execute(
                select(table.c.id).where(and_(table.c.id == document_id, table.c.club_id == club_id))
            ).first()
            if existing is None:
                return jsonify({'error': 'Document not found'}), 404

            ordered_ids = _fetch_ordered_document_ids(session, table, club_id)
            if document_id not in ordered_ids:
                return jsonify({'error': 'Document not found'}), 404

            ordered_ids.remove(document_id)
            insert_index = min(len(ordered_ids), max(0, requested_order - 1))
            ordered_ids.insert(insert_index, document_id)

            _rewrite_display_order(session, table, ordered_ids)
            session.commit()

            return jsonify({
                'message': 'Document order updated',
                'id': document_id,
                'displayOrder': insert_index + 1,
            })
        finally:
            session.close()

    return bp
