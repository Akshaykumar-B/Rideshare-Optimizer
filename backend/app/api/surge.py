"""Surge pricing API."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..services import surge_service

surge_bp = Blueprint('surge', __name__)


@surge_bp.route('/status', methods=['GET'])
@jwt_required()
def get_surge_status():
    """Get current surge multiplier for a location.

    Query params: lat, lng
    """
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    if lat is None or lng is None:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'lat and lng query params required'}), 400

    surge = surge_service.calculate_surge_for_location(lat, lng)
    return jsonify({'surge': surge}), 200


@surge_bp.route('/zones', methods=['GET'])
@jwt_required()
def get_surge_zones():
    """Get all surge zones for map overlay."""
    zones = surge_service.get_all_zone_surges()
    return jsonify({'zones': zones}), 200
