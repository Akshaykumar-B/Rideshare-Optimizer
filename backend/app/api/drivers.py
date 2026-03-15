"""Drivers API — availability, location updates."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User, DriverProfile

drivers_bp = Blueprint('drivers', __name__)


@drivers_bp.route('/availability', methods=['PUT'])
@jwt_required()
def toggle_availability():
    """Toggle driver availability."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or user.role != 'driver':
        return jsonify({'error': 'FORBIDDEN', 'message': 'Only drivers can toggle availability'}), 403

    profile = user.driver_profile
    if not profile:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'No driver profile found'}), 400

    data = request.get_json() or {}
    profile.is_available = data.get('is_available', not profile.is_available)

    db.session.commit()
    return jsonify({
        'message': f'Availability set to {profile.is_available}',
        'driver_profile': profile.to_dict()
    }), 200


@drivers_bp.route('/location', methods=['PUT'])
@jwt_required()
def update_location():
    """Update driver's current location."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or user.role != 'driver':
        return jsonify({'error': 'FORBIDDEN', 'message': 'Only drivers can update location'}), 403

    profile = user.driver_profile
    if not profile:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'No driver profile found'}), 400

    data = request.get_json()
    if not data or 'lat' not in data or 'lng' not in data:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'lat and lng are required'}), 400

    profile.current_lat = data['lat']
    profile.current_lng = data['lng']

    # Update H3 cell
    try:
        import h3
        profile.h3_cell = h3.latlng_to_cell(data['lat'], data['lng'], 7)
    except (ImportError, Exception):
        pass

    db.session.commit()
    return jsonify({'message': 'Location updated', 'driver_profile': profile.to_dict()}), 200


@drivers_bp.route('/current-trip', methods=['GET'])
@jwt_required()
def get_current_trip():
    """Get driver's active trip."""
    from ..models.trip import Trip

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or user.role != 'driver':
        return jsonify({'error': 'FORBIDDEN', 'message': 'Only drivers can view trips'}), 403

    profile = user.driver_profile
    if not profile:
        return jsonify({'trips': []}), 200

    active_trip = Trip.query.filter_by(
        driver_id=profile.id, status='active'
    ).first()

    if not active_trip:
        return jsonify({'trip': None}), 200

    return jsonify({'trip': active_trip.to_dict()}), 200
