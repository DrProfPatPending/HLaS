from flask import Blueprint, jsonify, request
from sqlalchemy import and_, select
from mini_site_pages import normalize_pages_config, get_enabled_pages, PAGE_TEMPLATES


def create_mini_site_routes(deps):
    bp = Blueprint('mini_sites', __name__)

    get_current_principal = deps['get_current_principal']
    get_postgres_backend = deps['get_postgres_backend']
    is_postgres_reads_enabled = deps['is_postgres_reads_enabled']
    is_postgres_writes_enabled = deps['is_postgres_writes_enabled']
    require_authenticated = deps['require_authenticated']
    require_permission = deps['require_permission']

    @bp.route('/mini-site', methods=['GET'])
    def get_mini_site_config():
        """Get mini site configuration for the authenticated user's club."""
        requested_club = str(request.args.get('club', '')).strip()
        auth_error = require_authenticated(requested_club)
        if auth_error:
            return auth_error

        principal = get_current_principal(requested_club)
        if principal is None:
            return jsonify({'error': 'Unauthorized'}), 401

        club_short_name = str(principal.get('scope_club_short_name') or principal.get('club_short_name') or '').strip()
        if not club_short_name:
            return jsonify({'error': 'Club is required'}), 400

        if not is_postgres_reads_enabled():
            return jsonify({'enabled': False, 'error': 'Mini site feature not available'}), 404

        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            clubs_table = backend['clubs_table']
            club_mini_sites_table = backend.get('club_mini_sites_table')

            if club_mini_sites_table is None:
                return jsonify({'enabled': False, 'error': 'Mini site table not available'}), 500

            # Get club id
            club_id = session.execute(
                select(clubs_table.c.id).where(
                    and_(clubs_table.c.short_name == club_short_name, clubs_table.c.is_active.is_(True))
                )
            ).scalar_one_or_none()

            if club_id is None:
                return jsonify({'error': 'Club not found'}), 404

            # Get mini site config
            row = session.execute(
                select(club_mini_sites_table).where(club_mini_sites_table.c.club_id == club_id)
            ).first()

            if row is None:
                # Return default (disabled) config
                return jsonify({
                    'enabled': False,
                    'title': '',
                    'tagline': '',
                    'hero_image_url': '',
                    'description': '',
                    'pages': normalize_pages_config([], club_short_name),
                    'social_links': {},
                })

            row_dict = row._mapping
            pages = normalize_pages_config(row_dict.get('pages', []), club_short_name)
            return jsonify({
                'id': row_dict.get('id'),
                'club_id': row_dict.get('club_id'),
                'enabled': row_dict.get('enabled', False),
                'title': row_dict.get('title', ''),
                'tagline': row_dict.get('tagline', ''),
                'hero_image_url': row_dict.get('hero_image_url', ''),
                'description': row_dict.get('description', ''),
                'pages': pages,
                'social_links': row_dict.get('social_links', {}),
            })

        finally:
            session.close()

    @bp.route('/mini-site', methods=['POST', 'PUT'])
    def update_mini_site_config():
        """Update mini site configuration for the authenticated user's club."""
        payload = request.json or {}
        requested_club = str(payload.get('club') or request.args.get('club') or '').strip()
        
        # Require club admin permission to update mini site
        auth_error = require_permission('club.update', requested_club)
        if auth_error:
            return auth_error

        principal = get_current_principal(requested_club)
        if principal is None:
            return jsonify({'error': 'Unauthorized'}), 401

        club_short_name = str(principal.get('scope_club_short_name') or principal.get('club_short_name') or '').strip()
        if not club_short_name:
            return jsonify({'error': 'Club is required'}), 400

        if not is_postgres_writes_enabled():
            return jsonify({'error': 'Mini site feature not available for writes'}), 500

        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            clubs_table = backend['clubs_table']
            club_mini_sites_table = backend.get('club_mini_sites_table')

            if club_mini_sites_table is None:
                return jsonify({'error': 'Mini site table not available'}), 500

            # Get club id
            club_id = session.execute(
                select(clubs_table.c.id).where(
                    and_(clubs_table.c.short_name == club_short_name, clubs_table.c.is_active.is_(True))
                )
            ).scalar_one_or_none()

            if club_id is None:
                return jsonify({'error': 'Club not found'}), 404

            # Extract configuration from payload
            enabled = bool(payload.get('enabled', False))
            title = str(payload.get('title', '')).strip()
            tagline = str(payload.get('tagline', '')).strip()
            hero_image_url = str(payload.get('hero_image_url', '')).strip()
            description = str(payload.get('description', '')).strip()
            
            # Handle pages: convert from frontend format (array of IDs) to internal format
            pages_input = payload.get('pages', []) if isinstance(payload.get('pages'), list) else []
            # If pages are IDs (strings), convert to page objects with enabled flag
            if pages_input and isinstance(pages_input[0], str):
                pages_input = [{'id': page_id, 'enabled': True} for page_id in pages_input]
            
            pages = normalize_pages_config(pages_input, club_short_name)
            social_links = payload.get('social_links', {}) if isinstance(payload.get('social_links'), dict) else {}

            # Check if mini site config exists
            existing = session.execute(
                select(club_mini_sites_table.c.id).where(club_mini_sites_table.c.club_id == club_id)
            ).first()

            if existing:
                # Update existing
                session.execute(
                    club_mini_sites_table.update()
                    .where(club_mini_sites_table.c.club_id == club_id)
                    .values(
                        enabled=enabled,
                        title=title,
                        tagline=tagline,
                        hero_image_url=hero_image_url,
                        description=description,
                        pages=pages,
                        social_links=social_links,
                    )
                )
            else:
                # Create new
                session.execute(
                    club_mini_sites_table.insert().values(
                        club_id=club_id,
                        enabled=enabled,
                        title=title,
                        tagline=tagline,
                        hero_image_url=hero_image_url,
                        description=description,
                        pages=pages,
                        social_links=social_links,
                    )
                )

            session.commit()

            return jsonify({
                'success': True,
                'enabled': enabled,
                'title': title,
                'tagline': tagline,
                'hero_image_url': hero_image_url,
                'description': description,
                'pages': pages,
                'social_links': social_links,
            })

        except Exception as e:
            session.rollback()
            return jsonify({'error': f'Failed to update mini site config: {str(e)}'}), 500
        finally:
            session.close()

    return bp
