import json
import mimetypes
import os
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from flask import Blueprint, Response, current_app, jsonify, request, send_file, send_from_directory
from sqlalchemy import and_, select

from db_models import club_logos, club_backgrounds
from routes.app_settings_routes import load_app_settings_config
from routes.field_order_routes import load_field_order_config


def create_public_blueprint(deps):
    bp = Blueprint('public', __name__)

    load_clubs_config = deps['load_clubs_config']
    normalize_what3words_words = deps['normalize_what3words_words']
    get_valid_club_short_names = deps['get_valid_club_short_names']
    APP_DATA_DIR = deps['APP_DATA_DIR']
    get_read_db_for_club = deps['get_read_db_for_club']
    get_column = deps['get_column']
    get_postgres_backend = deps['get_postgres_backend']
    is_postgres_reads_enabled = deps['is_postgres_reads_enabled']
    get_club_logo_path = deps['get_club_logo_path']
    CLUB_LOGOS_DIR = deps['CLUB_LOGOS_DIR']

    def _send_member_photo_from_file(club, filename):
        photo_dir = os.path.join(APP_DATA_DIR, 'ID_photos', club)
        if not os.path.isdir(photo_dir):
            return jsonify({'error': 'Photo directory not found'}), 404
        return send_from_directory(photo_dir, filename)

    def _get_member_photo_table():
        if not is_postgres_reads_enabled():
            return None
        backend = get_postgres_backend()
        return backend.get('member_photos_table')

    def _lookup_club_id(short_name):
        if not is_postgres_reads_enabled():
            return None
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            clubs_table = backend['clubs_table']
            return session.execute(
                select(clubs_table.c.id).where(
                    and_(clubs_table.c.short_name == short_name, clubs_table.c.is_active.is_(True))
                )
            ).scalar_one_or_none()
        finally:
            session.close()

    def _guess_mime_type(filename, fallback='image/jpeg'):
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or fallback

    @bp.route('/clubs', methods=['GET'])
    def get_clubs():
        return jsonify({'clubs': load_clubs_config()})

    @bp.route('/club/<club_short_name>/mini-site', methods=['GET'])
    def get_club_mini_site_config(club_short_name):
        """
        Public endpoint: Get mini site configuration for a club (if enabled).
        No authentication required.
        """
        if not is_postgres_reads_enabled():
            return jsonify({
                'enabled': False,
                'error': 'Mini site feature not available',
            }), 404

        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            clubs_table = backend['clubs_table']
            
            # Get club_id
            club_id = session.execute(
                select(clubs_table.c.id).where(
                    and_(clubs_table.c.short_name == club_short_name, clubs_table.c.is_active.is_(True))
                )
            ).scalar_one_or_none()
            
            if club_id is None:
                return jsonify({'error': 'Club not found'}), 404
            
            # Try to get mini site from PostgreSQL
            try:
                club_mini_sites_table = backend.get('club_mini_sites_table')
                if club_mini_sites_table is not None:
                    mini_site_row = session.execute(
                        select(club_mini_sites_table).where(club_mini_sites_table.c.club_id == club_id)
                    ).first()
                    
                    if mini_site_row is not None:
                        row_dict = mini_site_row._mapping.copy()
                        return jsonify({
                            'id': row_dict.get('id'),
                            'club_id': row_dict.get('club_id'),
                            'enabled': row_dict.get('enabled', False),
                            'title': row_dict.get('title', ''),
                            'tagline': row_dict.get('tagline', ''),
                            'hero_image_url': row_dict.get('hero_image_url', ''),
                            'description': row_dict.get('description', ''),
                            'pages': row_dict.get('pages', []),
                            'social_links': row_dict.get('social_links', {}),
                        })
            except Exception as e:
                current_app.logger.error(f"Error fetching mini site from PostgreSQL: {e}")
            
            # Mini site not configured yet
            return jsonify({
                'enabled': False,
                'error': 'Mini site not configured for this club',
            }), 404
            
        finally:
            session.close()

    @bp.route('/field-order', methods=['GET'])
    def get_field_order():
        try:
            return jsonify({'field_order': load_field_order_config(deps)})
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    @bp.route('/app-settings', methods=['GET'])
    def get_app_settings():
        try:
            return jsonify({'settings': load_app_settings_config(deps)})
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    @bp.route('/w3w/coordinates', methods=['GET'])
    def w3w_coordinates():
        words_param = request.args.get('words', '')
        words = normalize_what3words_words(words_param)
        if not words:
            return jsonify({'error': 'Invalid what3words address'}), 400

        api_key = os.getenv('WHAT3WORDS_API_KEY', '').strip()
        if not api_key:
            return jsonify({
                'words': words,
                'lat': None,
                'lng': None,
                'available': False,
                'reason': 'WHAT3WORDS_API_KEY is not configured',
            })

        lookup_url = (
            'https://api.what3words.com/v3/convert-to-coordinates'
            f'?words={quote(words)}&key={quote(api_key)}'
        )

        try:
            with urlopen(lookup_url, timeout=8) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode('utf-8'))
            except Exception:
                payload = {'error': str(exc)}
            return jsonify({'error': payload.get('error', 'Failed to resolve what3words')}), 502
        except URLError:
            return jsonify({'error': 'Unable to reach what3words service'}), 502
        except Exception:
            return jsonify({'error': 'Failed to resolve what3words'}), 502

        coordinates = payload.get('coordinates', {}) if isinstance(payload, dict) else {}
        lat = coordinates.get('lat')
        lng = coordinates.get('lng')
        if lat is None or lng is None:
            return jsonify({'error': 'No coordinates returned for what3words'}), 404

        return jsonify({'words': words, 'lat': lat, 'lng': lng})

    @bp.route('/member_photo/<club>/<path:filename>', methods=['GET'])
    def member_photo(club, filename):
        valid_clubs = get_valid_club_short_names()
        if club not in valid_clubs:
            return jsonify({'error': 'Invalid club'}), 404
        member_photos_table = _get_member_photo_table()
        club_id = _lookup_club_id(club)
        if member_photos_table is not None and club_id is not None:
            backend = get_postgres_backend()
            session = backend['session_factory']()
            try:
                row = session.execute(
                    select(
                        member_photos_table.c.image_data,
                        member_photos_table.c.mime_type,
                        member_photos_table.c.filename,
                    ).where(
                        and_(
                            member_photos_table.c.club_id == club_id,
                            member_photos_table.c.filename == filename,
                        )
                    )
                ).first()
            finally:
                session.close()

            if row is not None:
                return Response(row.image_data, mimetype=row.mime_type or _guess_mime_type(row.filename))

        return _send_member_photo_from_file(club, filename)

    @bp.route('/member_photo_for_member/<club>/<member_id>', methods=['GET'])
    def member_photo_for_member(club, member_id):
        valid_clubs = get_valid_club_short_names()
        if club not in valid_clubs:
            return jsonify({'error': 'Invalid club'}), 404

        member_photos_table = _get_member_photo_table()
        club_id = _lookup_club_id(club)
        if member_photos_table is not None and club_id is not None:
            backend = get_postgres_backend()
            session = backend['session_factory']()
            try:
                row = session.execute(
                    select(
                        member_photos_table.c.image_data,
                        member_photos_table.c.mime_type,
                        member_photos_table.c.filename,
                    ).where(
                        and_(
                            member_photos_table.c.club_id == club_id,
                            member_photos_table.c.member_id == int(member_id),
                        )
                    )
                ).first()
            except Exception:
                row = None
            finally:
                session.close()

            if row is not None:
                return Response(row.image_data, mimetype=row.mime_type or _guess_mime_type(row.filename))

        db_info = get_read_db_for_club(club)
        session = db_info['session']
        members_table = db_info['members_table']
        Member = db_info['Member']

        id_column = get_column('ID', members_table)
        if id_column is None:
            id_column = get_column('id', members_table)
        number_column = get_column('Number', members_table)
        photo_column = get_column('Photo_Path', members_table)
        if photo_column is None:
            photo_column = get_column('photo_path', members_table)
        if photo_column is None or (id_column is None and number_column is None):
            try:
                session.close()
            except Exception:
                pass
            return jsonify({'error': 'Photo columns not available'}), 404

        member = None
        try:
            target_member_id = int(member_id)

            if id_column is not None:
                member = session.scalars(select(Member).where(id_column == target_member_id)).first()
            if member is None and number_column is not None:
                member = session.scalars(select(Member).where(number_column == str(member_id))).first()
        except (TypeError, ValueError):
            member = None
        finally:
            session.close()

        if member is None:
            return jsonify({'error': 'Member not found'}), 404

        photo_name = str(getattr(member, photo_column.name, '') or '').strip()
        if not photo_name:
            return jsonify({'error': 'No member photo'}), 404

        return _send_member_photo_from_file(club, photo_name)

    @bp.route('/club_logo/<short_name>', methods=['GET'])
    def club_logo(short_name):
        import logging
        logger = logging.getLogger("club_logo")
        logger.debug(f"Request for club logo: {short_name}")
        
        # Fallback path for filesystem logos
        logo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'club_logos')
        if not os.path.exists(logo_dir):
            logo_dir = os.path.join(os.path.dirname(__file__), '..', 'club_logos')
        if not os.path.exists(logo_dir):
            logo_dir = '/app/club_logos'
        
        logo_path = os.path.join(logo_dir, f'{short_name}.png')
        
        # Try database first, then filesystem
        db_engine = deps.get('db_engine')
        logger.debug(f"db_engine from deps: {db_engine}")
        if db_engine is None:
            db_engine = getattr(current_app, 'db_engine', None)
            logger.debug(f"db_engine from current_app: {db_engine}")
        
        # Try database
        if db_engine is not None:
            try:
                with db_engine.connect() as conn:
                    stmt = select(
                        club_logos.c.image_data,
                        club_logos.c.mime_type
                    ).where(club_logos.c.club_short_name == short_name)
                    logger.debug(f"SQL statement: {stmt}")
                    result = conn.execute(stmt).first()
                    logger.debug(f"Query result: {result}")
                    if result:
                        image_data, mime_type = result
                        logger.debug(f"image_data type: {type(image_data)}, mime_type: {mime_type}")
                        return send_file(BytesIO(image_data), mimetype=mime_type)
            except Exception as e:
                logger.debug(f"Database lookup failed, trying filesystem: {e}")
        
        # Fall back to filesystem
        if os.path.isfile(logo_path):
            try:
                with open(logo_path, 'rb') as f:
                    image_data = f.read()
                mime_type = 'image/png'
                logger.debug(f"Loaded logo from filesystem: {logo_path}")
                return send_file(BytesIO(image_data), mimetype=mime_type)
            except Exception as e:
                logger.error(f"Error reading logo file: {e}")
        
        logger.warning(f"Logo not found for club: {short_name}")
        return jsonify({'error': 'Logo not found'}), 404

    @bp.route('/club_background/<short_name>', methods=['GET'])
    def club_background(short_name):
        import logging
        logger = logging.getLogger("club_background")
        logger.debug(f"Request for club background: {short_name}")
        
        # Fallback path for filesystem backgrounds
        logo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'club_logos')
        if not os.path.exists(logo_dir):
            logo_dir = os.path.join(os.path.dirname(__file__), '..', 'club_logos')
        if not os.path.exists(logo_dir):
            logo_dir = '/app/club_logos'
        
        bg_path = os.path.join(logo_dir, f'{short_name}_background.png')
        
        # Try database first, then filesystem
        db_engine = deps.get('db_engine')
        logger.debug(f"db_engine from deps: {db_engine}")
        if db_engine is None:
            db_engine = getattr(current_app, 'db_engine', None)
            logger.debug(f"db_engine from current_app: {db_engine}")
        
        # Try database
        if db_engine is not None:
            try:
                with db_engine.connect() as conn:
                    stmt = select(
                        club_backgrounds.c.image_data,
                        club_backgrounds.c.mime_type
                    ).where(club_backgrounds.c.club_short_name == short_name)
                    logger.debug(f"SQL statement: {stmt}")
                    result = conn.execute(stmt).first()
                    logger.debug(f"Query result: {result}")
                    if result:
                        image_data, mime_type = result
                        logger.debug(f"image_data type: {type(image_data)}, mime_type: {mime_type}")
                        return send_file(BytesIO(image_data), mimetype=mime_type)
            except Exception as e:
                logger.debug(f"Database lookup failed, trying filesystem: {e}")
        
        # Fall back to filesystem
        if os.path.isfile(bg_path):
            try:
                with open(bg_path, 'rb') as f:
                    image_data = f.read()
                mime_type = 'image/png'
                logger.debug(f"Loaded background from filesystem: {bg_path}")
                return send_file(BytesIO(image_data), mimetype=mime_type)
            except Exception as e:
                logger.error(f"Error reading background file: {e}")
        
        logger.warning(f"Background not found for club: {short_name}")
        return jsonify({'error': 'Background not found'}), 404

    return bp
