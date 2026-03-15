"""Riders API — ride request CRUD."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.ride_request import RideRequest

riders_bp = Blueprint('riders', __name__)


@riders_bp.route('/request', methods=['POST'])
@jwt_required()
def create_ride_request():
    """Create a new ride request."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'No data provided'}), 400

    required = ['pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng']
    for field in required:
        if field not in data:
            return jsonify({'error': 'VALIDATION_ERROR', 'message': f'{field} is required'}), 400

    # H3 cell for spatial indexing
    h3_cell = None
    try:
        import h3
        h3_cell = h3.latlng_to_cell(data['pickup_lat'], data['pickup_lng'], 7)
    except (ImportError, Exception):
        pass

    ride = RideRequest(
        rider_id=user_id,
        pickup_lat=data['pickup_lat'],
        pickup_lng=data['pickup_lng'],
        dropoff_lat=data['dropoff_lat'],
        dropoff_lng=data['dropoff_lng'],
        pickup_address=data.get('pickup_address'),
        dropoff_address=data.get('dropoff_address'),
        pickup_h3_cell=h3_cell,
        status='pending',
    )
    db.session.add(ride)
    db.session.commit()

    return jsonify({'message': 'Ride request created', 'ride': ride.to_dict()}), 201


@riders_bp.route('/my-requests', methods=['GET'])
@jwt_required()
def get_my_requests():
    """Get current user's ride requests."""
    user_id = int(get_jwt_identity())
    rides = RideRequest.query.filter_by(rider_id=user_id).order_by(
        RideRequest.created_at.desc()
    ).limit(50).all()

    return jsonify({'rides': [r.to_dict() for r in rides]}), 200


@riders_bp.route('/<int:ride_id>', methods=['GET'])
@jwt_required()
def get_ride_request(ride_id):
    """Get a specific ride request."""
    ride = RideRequest.query.get_or_404(ride_id)
    return jsonify({'ride': ride.to_dict()}), 200


@riders_bp.route('/<int:ride_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_ride(ride_id):
    """Cancel a ride request."""
    user_id = int(get_jwt_identity())
    ride = RideRequest.query.get_or_404(ride_id)

    if ride.rider_id != user_id:
        return jsonify({'error': 'FORBIDDEN', 'message': 'Not your ride request'}), 403

    if ride.status not in ('pending', 'matched'):
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'Cannot cancel a ride in progress'}), 400

    ride.status = 'cancelled'
    db.session.commit()

    return jsonify({'message': 'Ride cancelled', 'ride': ride.to_dict()}), 200
