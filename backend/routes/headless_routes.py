"""
Headless API routes for WordPress integration.

These endpoints provide clean JSON responses without framework-specific
formatting, designed for consumption by WordPress plugins and other
external integrations.

Authentication:
- WordPress nonces (initial implementation)
- HLaS member tokens (long-term implementation)
"""

import os
from flask import Blueprint, jsonify, request
from sqlalchemy import and_, select
import logging

logger = logging.getLogger(__name__)


def create_headless_blueprint(deps):
    """Create a blueprint for headless/WordPress integration routes."""
    bp = Blueprint('headless', __name__, url_prefix='/api/headless')

    get_valid_club_short_names = deps['get_valid_club_short_names']
    get_postgres_backend = deps['get_postgres_backend']
    get_current_principal = deps['get_current_principal']
    extract_bearer_token = deps['extract_bearer_token']
    is_postgres_reads_enabled = deps['is_postgres_reads_enabled']
    _resolve_postgres_club_id = deps['_resolve_postgres_club_id']

    # ============================================================================
    # WordPress Authentication Bridge
    # ============================================================================

    def verify_wordpress_nonce(nonce_value, action='hlas_integration', user_id=None):
        """
        Verify a WordPress nonce.
        
        For MVP, this accepts nonces from either:
        1. A shared WordPress instance (verification via callback)
        2. A pre-shared API token approach
        
        In production, consider:
        - Shared secret between WordPress and HLaS
        - Callback to WordPress to verify nonce
        - JWT-style token from WordPress
        
        Args:
            nonce_value: The nonce string from WordPress
            action: The action this nonce validates
            user_id: Optional WordPress user ID
        
        Returns:
            bool: True if nonce is valid, False otherwise
        """
        # For MVP: Accept nonce if a valid shared API key is also provided
        wordpress_api_key = os.getenv('WORDPRESS_API_KEY', '').strip()
        
        if wordpress_api_key:
            # Verify API key from request header
            api_key_header = request.headers.get('X-WordPress-API-Key', '').strip()
            if api_key_header == wordpress_api_key:
                return True
        
        # TODO: Implement full nonce verification
        # - Call WordPress REST API: /wp-json/hlas/v1/verify-nonce
        # - Or use shared secret to validate nonce signature
        # - Or check against cached nonce list
        
        return False

    def get_wp_auth_context():
        """
        Extract authentication context from WordPress request.
        
        Supports:
        1. WordPress nonce (X-WordPress-Nonce header)
        2. WordPress API key (X-WordPress-API-Key header)
        3. HLaS member token (Authorization: Bearer header)
        
        Returns:
            dict with auth mode and user context, or None if unauthenticated
        """
        # Check for WordPress nonce
        wp_nonce = request.headers.get('X-WordPress-Nonce', '').strip()
        wp_user_id = request.headers.get('X-WP-User-ID', '').strip()
        wp_api_key = request.headers.get('X-WordPress-API-Key', '').strip()
        
        if wp_nonce and wp_user_id:

            # TODO: Validate WordPress nonce signature
            # For now, nonce presence indicates WordPress integration
            return {
                'mode': 'wordpress_nonce',
                'wp_nonce': wp_nonce,
                'wp_user_id': wp_user_id,
            }
        
        # Fall back to HLaS member token
        token = extract_bearer_token()
        if token:
            return {
                'mode': 'hlas_token',
                'token': token,
            }
        
        return None

    def get_member_context_for_club(club_short_name):
        """
        Get the current member context for permission checks.
        
        Returns:
            dict with member_id and club info, or None
        """
        # Try to get HLaS member context
        principal = get_current_principal(club_short_name)
        if principal:
            return {
                'member_id': principal.get('member_id'),
                'club': club_short_name,
                'user_type': 'hlas_member',
            }
        
        # TODO: Map WordPress user to HLaS member
        # For now, WordPress requests are treated as public/limited access
        return None

    # ============================================================================
    # Beat Details Endpoint
    # ============================================================================

    @bp.route('/beat-details/<club_short_name>', methods=['GET'])
    def get_beat_details_headless(club_short_name):
        """
        Get beat details for a club in headless format.
        
        REQUIRES AUTHENTICATION: This is a members-only endpoint. Non-authenticated
        requests receive a fallback message with club contact information.
        
        Response format: Clean JSON with no framework-specific markup.
        
        Authenticated response:
            {
                "club": {"id": 1, "name": "...", "short_name": "..."},
                "beats": [
                    {
                        "id": 1,
                        "name": "...",
                        "position": "...",
                        "description": "...",
                        "coordinates": {"lat": 0.0, "lng": 0.0},
                        "river": "...",
                        "parking_locations": [...],
                        "waypoints": [...]
                    }
                ]
            }
        
        Unauthenticated response (members_only flag):
            {
                "members_only": true,
                "club": {"name": "...", "short_name": "..."},
                "message": "This information is only available to members of <Club Name>. Please contact <admin_email> for any membership enquiries or questions on using the website."
            }
        """
        # Validate club exists
        valid_clubs = get_valid_club_short_names()
        if club_short_name not in valid_clubs:
            return jsonify({'error': 'Club not found'}), 404

        # Try to get club data from PostgreSQL (needed for authentication check)
        if not is_postgres_reads_enabled():
            return jsonify({
                'error': 'Beat data unavailable',
                'club': club_short_name,
                'beats': []
            }), 503

        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            clubs_table = backend['clubs_table']
            club_beats_table = backend['club_beats_table']
            
            # Get club data (needed for both auth check and response)
            club_row = session.execute(
                select(clubs_table).where(clubs_table.c.short_name == club_short_name)
            ).first()
            
            if not club_row:
                return jsonify({
                    'error': 'Club not found',
                    'club': club_short_name,
                    'beats': []
                }), 404
            
            # Check authentication - member-only access
            auth_context = get_wp_auth_context()
            member_context = get_member_context_for_club(club_short_name) if auth_context else None
            
            is_authenticated = auth_context is not None and member_context is not None
            
            # If not authenticated, return members-only fallback message
            if not is_authenticated:
                contact_email = club_row.admin_email or 'membership@example.com'
                return jsonify({
                    'members_only': True,
                    'club': {
                        'name': club_row.full_name,
                        'short_name': club_row.short_name,
                    },
                    'message': f'This information is only available to members of {club_row.full_name}. Please contact {contact_email} for any membership enquiries or questions on using the website.',
                }), 403
            
            # Authenticated: Get beats for this club
            beat_rows = session.execute(
                select(club_beats_table).where(
                    club_beats_table.c.club_id == club_row.id
                )
            ).fetchall()
            
            # Format beats for headless consumption
            beats = []
            for row in beat_rows:
                beat = {
                    'id': row.id,
                    'name': row.beat_name or '',
                    'beat_id': row.beat_id or '',
                    'position': row.position or '',
                    'description': row.beat_description or '',
                    'detailed_description': row.detailed_description or '',
                    'river': row.river or '',
                    'coordinates': {
                        'upstream': {
                            'latitude': float(row.beat_upstream_latitude) if row.beat_upstream_latitude else None,
                            'longitude': float(row.beat_upstream_longitude) if row.beat_upstream_longitude else None,
                        },
                        'downstream': {
                            'latitude': float(row.beat_downstream_latitude) if row.beat_downstream_latitude else None,
                            'longitude': float(row.beat_downstream_longitude) if row.beat_downstream_longitude else None,
                        },
                    },
                    'parking_locations': row.parking_locations or [],
                    'waypoints': row.waypoints or [],
                }
                beats.append(beat)
            
            return jsonify({
                'club': {
                    'id': club_row.id,
                    'name': club_row.full_name,
                    'short_name': club_row.short_name,
                    'description': club_row.description or '',
                },
                'beats': beats,
            })
        
        except Exception as exc:
            logger.error(f'Error fetching beat details for {club_short_name}: {exc}')
            return jsonify({
                'error': 'Failed to fetch beat details',
                'club': club_short_name,
                'beats': []
            }), 500
        
        finally:
            session.close()

    # ============================================================================
    # Catch Returns Endpoint
    # ============================================================================

    @bp.route('/catch-returns/<club_short_name>', methods=['GET'])
    def get_catch_returns_headless(club_short_name):
        """
        Get catch returns for the current member in headless format.
        
        Requires authentication (HLaS token or valid WordPress nonce).
        
        Query params:
            - limit: max results (default 50, max 200)
            - offset: pagination offset (default 0)
        
        Returns:
            {
                "club": {...},
                "member": {"id": 1, "name": "..."},
                "returns": [
                    {
                        "id": 1,
                        "session_date": "YYYY-MM-DD",
                        "beat_id": "...",
                        "fish_count": {
                            "small_trout": 0,
                            "medium_trout": 0,
                            "large_trout": 0,
                            "small_grayling": 0,
                            "medium_grayling": 0,
                            "large_grayling": 0,
                            "other_fish": 0
                        },
                        "notes": {
                            "flies_used": "...",
                            "weather": "...",
                            "predator_damage": "..."
                        },
                        "created_at": "ISO datetime"
                    }
                ]
            }
        """
        # Validate club exists
        valid_clubs = get_valid_club_short_names()
        if club_short_name not in valid_clubs:
            return jsonify({'error': 'Club not found'}), 404
        
        # Require authentication
        auth_context = get_wp_auth_context()
        if not auth_context:
            return jsonify({'error': 'Unauthorized - authentication required'}), 401
        
        # Get member context
        member_context = get_member_context_for_club(club_short_name)
        if not member_context:
            return jsonify({'error': 'User has no member access for this club'}), 403
        
        member_id = member_context['member_id']
        
        # Parse pagination params
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        if not limit or limit < 1:
            limit = 50
        limit = min(limit, 200)
        
        if offset < 0:
            offset = 0
        
        if not is_postgres_reads_enabled():
            return jsonify({
                'error': 'Catch return data unavailable',
                'club': club_short_name,
                'returns': []
            }), 503
        
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            clubs_table = backend['clubs_table']
            catch_returns_table = backend['catch_returns_table']
            
            # Get club ID
            club_id = _resolve_postgres_club_id(session, club_short_name)
            if club_id is None:
                return jsonify({
                    'error': 'Club not found',
                    'club': club_short_name,
                    'returns': []
                }), 404
            
            # Get club data
            club_row = session.execute(
                select(clubs_table).where(clubs_table.c.id == club_id)
            ).first()
            
            # Fetch catch returns for this member
            catch_rows = session.execute(
                select(catch_returns_table)
                .where(
                    and_(
                        catch_returns_table.c.club_id == club_id,
                        catch_returns_table.c.member_id == int(member_id),
                    )
                )
                .order_by(
                    catch_returns_table.c.session_date.desc(),
                    catch_returns_table.c.created_at.desc()
                )
                .offset(offset)
                .limit(limit)
            ).fetchall()
            
            # Format returns for headless consumption
            returns = []
            for row in catch_rows:
                catch_return = {
                    'id': row.id,
                    'session_date': str(row.session_date) if row.session_date else None,
                    'beat_id': str(row.beat_id) if row.beat_id else None,
                    'fish_count': {
                        'small_trout': int(row.small_trout or 0),
                        'medium_trout': int(row.medium_trout or 0),
                        'large_trout': int(row.large_trout or 0),
                        'small_grayling': int(row.small_grayling or 0),
                        'medium_grayling': int(row.medium_grayling or 0),
                        'large_grayling': int(row.large_grayling or 0),
                        'other_fish': int(row.other_fish or 0),
                    },
                    'notes': {
                        'flies_used': str(row.flies_used or ''),
                        'weather': str(row.weather_conditions or ''),
                        'predator_damage': str(row.predator_damage or ''),
                    },
                    'created_at': str(row.created_at) if row.created_at else None,
                }
                returns.append(catch_return)
            
            # Get total count for pagination
            total_count = session.execute(
                select(catch_returns_table.c.id)
                .where(
                    and_(
                        catch_returns_table.c.club_id == club_id,
                        catch_returns_table.c.member_id == int(member_id),
                    )
                )
            ).rowcount
            
            return jsonify({
                'club': {
                    'id': club_row.id,
                    'name': club_row.full_name,
                    'short_name': club_row.short_name,
                },
                'member': {
                    'id': member_id,
                },
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': total_count,
                },
                'returns': returns,
            })
        
        except Exception as exc:
            logger.error(f'Error fetching catch returns for member {member_id}: {exc}')
            return jsonify({
                'error': 'Failed to fetch catch returns',
                'club': club_short_name,
                'returns': []
            }), 500
        
        finally:
            session.close()

    @bp.route('/catch-returns/<club_short_name>', methods=['POST'])
    def create_catch_return_headless(club_short_name):
        """
        Create a new catch return entry.
        
        Requires authentication (HLaS token or valid WordPress nonce).
        
        Request body:
            {
                "session_date": "YYYY-MM-DD",
                "beat_id": "...",
                "fish_count": {
                    "small_trout": 0,
                    "medium_trout": 0,
                    "large_trout": 0,
                    "small_grayling": 0,
                    "medium_grayling": 0,
                    "large_grayling": 0,
                    "other_fish": 0
                },
                "flies_used": "...",
                "weather_conditions": "...",
                "predator_damage": "..."
            }
        
        Returns: Created catch return object with ID
        """
        # Validate club exists
        valid_clubs = get_valid_club_short_names()
        if club_short_name not in valid_clubs:
            return jsonify({'error': 'Club not found'}), 404
        
        # Require authentication
        auth_context = get_wp_auth_context()
        if not auth_context:
            return jsonify({'error': 'Unauthorized - authentication required'}), 401
        
        # Get member context
        member_context = get_member_context_for_club(club_short_name)
        if not member_context:
            return jsonify({'error': 'User has no member access for this club'}), 403
        
        member_id = member_context['member_id']
        
        # Parse request data
        data = request.json or {}
        
        session_date_str = str(data.get('session_date', '')).strip()
        if not session_date_str:
            return jsonify({'error': 'session_date is required (YYYY-MM-DD format)'}), 400
        
        try:
            from datetime import datetime
            session_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'session_date must be in YYYY-MM-DD format'}), 400
        
        beat_id = str(data.get('beat_id', '')).strip()
        
        # Extract fish counts
        fish_count = data.get('fish_count', {})
        small_trout = int(fish_count.get('small_trout', 0) or 0)
        medium_trout = int(fish_count.get('medium_trout', 0) or 0)
        large_trout = int(fish_count.get('large_trout', 0) or 0)
        small_grayling = int(fish_count.get('small_grayling', 0) or 0)
        medium_grayling = int(fish_count.get('medium_grayling', 0) or 0)
        large_grayling = int(fish_count.get('large_grayling', 0) or 0)
        other_fish = int(fish_count.get('other_fish', 0) or 0)
        
        # Validate fish counts are non-negative
        for count in [small_trout, medium_trout, large_trout, small_grayling, 
                      medium_grayling, large_grayling, other_fish]:
            if count < 0:
                return jsonify({'error': 'Fish counts cannot be negative'}), 400
        
        # Extract notes
        flies_used = str(data.get('flies_used', '')).strip()[:500]
        weather_conditions = str(data.get('weather_conditions', '')).strip()[:500]
        predator_damage = str(data.get('predator_damage', '')).strip()[:500]
        
        if not is_postgres_reads_enabled():
            return jsonify({'error': 'Service unavailable'}), 503
        
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            catch_returns_table = backend['catch_returns_table']
            
            # Get club ID
            club_id = _resolve_postgres_club_id(session, club_short_name)
            if club_id is None:
                return jsonify({'error': 'Club not found'}), 404
            
            # Insert catch return
            from sqlalchemy import text
            result = session.execute(
                text('''
                    INSERT INTO catch_returns (
                        club_id, member_id, session_date, beat_id,
                        small_trout, medium_trout, large_trout,
                        small_grayling, medium_grayling, large_grayling,
                        other_fish, flies_used, weather_conditions,
                        predator_damage, created_at
                    )
                    VALUES (
                        :club_id, :member_id, :session_date, :beat_id,
                        :small_trout, :medium_trout, :large_trout,
                        :small_grayling, :medium_grayling, :large_grayling,
                        :other_fish, :flies_used, :weather_conditions,
                        :predator_damage, CURRENT_TIMESTAMP
                    )
                    RETURNING id
                '''),
                {
                    'club_id': club_id,
                    'member_id': int(member_id),
                    'session_date': session_date.isoformat(),
                    'beat_id': beat_id,
                    'small_trout': small_trout,
                    'medium_trout': medium_trout,
                    'large_trout': large_trout,
                    'small_grayling': small_grayling,
                    'medium_grayling': medium_grayling,
                    'large_grayling': large_grayling,
                    'other_fish': other_fish,
                    'flies_used': flies_used,
                    'weather_conditions': weather_conditions,
                    'predator_damage': predator_damage,
                }
            )
            
            catch_return_id = result.scalar()
            session.commit()
            
            return jsonify({
                'status': 'success',
                'catch_return_id': catch_return_id,
                'session_date': session_date_str,
            }), 201
        
        except Exception as exc:
            session.rollback()
            logger.error(f'Error creating catch return: {exc}')
            return jsonify({'error': 'Failed to create catch return'}), 500
        
        finally:
            session.close()

    return bp
