"""Trips API — trip lifecycle."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from ..extensions import db
from ..models.trip import Trip, TripRider
from ..models.ride_request import RideRequest

trips_bp = Blueprint('trips', __name__)


@trips_bp.route('/<int:trip_id>', methods=['GET'])
@jwt_required()
def get_trip(trip_id):
    """Get trip details with route, riders, and fares."""
    trip = Trip.query.get_or_404(trip_id)
    return jsonify({'trip': trip.to_dict()}), 200


@trips_bp.route('/<int:trip_id>/complete', methods=['PUT'])
@jwt_required()
def complete_trip(trip_id):
    """Mark a trip as completed."""
    trip = Trip.query.get_or_404(trip_id)

    if trip.status != 'active':
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'Trip is not active'}), 400

    trip.status = 'completed'
    trip.completed_at = datetime.now(timezone.utc)

    # Update ride request statuses
    for tr in trip.riders:
        ride = RideRequest.query.get(tr.ride_request_id)
        if ride:
            ride.status = 'completed'

    db.session.commit()
    return jsonify({'message': 'Trip completed', 'trip': trip.to_dict()}), 200


@trips_bp.route('/<int:trip_id>/carbon', methods=['GET'])
@jwt_required()
def get_trip_carbon(trip_id):
    """Get CO₂ savings for a specific trip."""
    from ..services import carbon_service

    trip = Trip.query.get_or_404(trip_id)
    riders_metrics = []
    for tr in trip.riders:
        riders_metrics.append({
            'direct_distance_km': tr.direct_distance_km or 0,
        })

    savings = carbon_service.calculate_carbon_savings(
        riders_metrics, trip.total_distance_km or 0
    )
    return jsonify({'carbon_savings': savings}), 200
