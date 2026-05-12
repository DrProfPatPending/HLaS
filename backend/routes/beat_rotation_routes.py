"""Beat map rotation API routes"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)


def create_beat_rotation_blueprint(route_deps):
    """Create a blueprint for beat map rotation routes"""
    beat_rotation_bp = Blueprint('beat_rotation', __name__)
    db_engine = route_deps.get('db_engine')

    @beat_rotation_bp.route('/api/beat/<int:beat_id>/map-rotation', methods=['GET'])
    def get_beat_map_rotation(beat_id):
        """Get the default map rotation for a beat"""
        try:
            from db_models import beat_map_rotations
            
            with db_engine.connect() as conn:
                result = conn.execute(
                    beat_map_rotations.select().where(
                        beat_map_rotations.c.beat_id == beat_id
                    )
                ).fetchone()
                
                if result:
                    return jsonify({
                        'beat_id': beat_id,
                        'rotation_bearing': result.rotation_bearing
                    }), 200
                else:
                    return jsonify({
                        'beat_id': beat_id,
                        'rotation_bearing': 0
                    }), 200
        except Exception as e:
            logger.error(f'Error fetching beat rotation: {e}')
            return jsonify({'error': 'Failed to fetch beat rotation'}), 500

    @beat_rotation_bp.route('/api/beat/<int:beat_id>/map-rotation', methods=['PUT'])
    def update_beat_map_rotation(beat_id):
        """Update the default map rotation for a beat"""
        try:
            data = request.get_json() or {}
            rotation = data.get('rotation_bearing', 0)
            
            # Validate rotation is an integer between 0-359
            try:
                rotation = int(rotation)
                rotation = rotation % 360  # Normalize to 0-359 range
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid rotation value'}), 400
            
            from db_models import beat_map_rotations
            
            with db_engine.begin() as conn:
                # Check if rotation exists
                existing = conn.execute(
                    beat_map_rotations.select().where(
                        beat_map_rotations.c.beat_id == beat_id
                    )
                ).fetchone()
                
                if existing:
                    conn.execute(
                        beat_map_rotations.update().where(
                            beat_map_rotations.c.beat_id == beat_id
                        ).values(rotation_bearing=rotation)
                    )
                else:
                    conn.execute(
                        beat_map_rotations.insert().values(
                            beat_id=beat_id,
                            rotation_bearing=rotation
                        )
                    )
                
                return jsonify({
                    'beat_id': beat_id,
                    'rotation_bearing': rotation
                }), 200
        except Exception as e:
            logger.error(f'Error updating beat rotation: {e}')
            return jsonify({'error': 'Failed to update beat rotation'}), 500

    return beat_rotation_bp
