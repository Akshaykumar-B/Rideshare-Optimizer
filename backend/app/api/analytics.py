"""Analytics API — DP vs Greedy comparison, heatmap, carbon summary."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..services import dp_optimizer, greedy_optimizer, fare_service, carbon_service, surge_service

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/compare', methods=['POST'])
@jwt_required()
def compare_algorithms():
    """Run DP + both greedy algorithms on the same rider set.

    Request body:
    {
        "driver_start": {"lat": 12.93, "lng": 77.62},
        "riders": [
            {"pickup_lat": ..., "pickup_lng": ..., "dropoff_lat": ..., "dropoff_lng": ...,
             "pickup_address": "...", "dropoff_address": "...", "rider_id": 1},
            ...
        ],
        "vehicle_capacity": 4
    }

    Returns: DP result, NN result, CI result, fares, carbon savings, comparison metrics.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'No data provided'}), 400

    driver_start_data = data.get('driver_start', {})
    driver_start = (driver_start_data.get('lat', 12.9352), driver_start_data.get('lng', 77.6245))
    riders = data.get('riders', [])
    capacity = data.get('vehicle_capacity', 4)

    if not riders:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'At least one rider required'}), 400

    if len(riders) > 8:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'Maximum 8 riders for DP comparison'}), 400

    # Run all three algorithms
    dp_result = dp_optimizer.optimize(driver_start, riders, capacity)
    nn_result = greedy_optimizer.nearest_neighbor(driver_start, riders, capacity)
    ci_result = greedy_optimizer.cheapest_insertion(driver_start, riders, capacity)

    # Calculate fares for DP route
    fares = []
    shapley = []
    carbon = {}

    if dp_result and dp_result.get('feasible'):
        fares = fare_service.calculate_shared_fares(riders, dp_result)
        try:
            shapley = fare_service.calculate_shapley_values(riders, driver_start, capacity)
        except Exception:
            shapley = []

        carbon = carbon_service.calculate_carbon_savings(
            dp_result.get('rider_metrics', []),
            dp_result.get('total_distance_km', 0)
        )

    # Compute optimality gaps
    comparison = _compute_comparison(dp_result, nn_result, ci_result)

    # Surge info for driver start location
    surge = surge_service.calculate_surge_for_location(driver_start[0], driver_start[1])

    return jsonify({
        'dp': dp_result,
        'nearest_neighbor': nn_result,
        'cheapest_insertion': ci_result,
        'fares': fares,
        'shapley_values': shapley,
        'carbon_savings': carbon,
        'comparison': comparison,
        'surge': surge,
    }), 200


@analytics_bp.route('/heatmap', methods=['GET'])
@jwt_required()
def get_heatmap():
    """Get demand heatmap data."""
    zones = surge_service.get_all_zone_surges()
    return jsonify({'zones': zones}), 200


@analytics_bp.route('/carbon-summary', methods=['GET'])
@jwt_required()
def get_carbon_summary():
    """Get platform-wide CO₂ savings statistics."""
    summary = carbon_service.get_platform_carbon_summary()
    return jsonify({'carbon_summary': summary}), 200


def _compute_comparison(dp_result, nn_result, ci_result):
    """Compute optimality gap and comparison metrics."""
    if not dp_result or not dp_result.get('feasible'):
        return {'message': 'DP solution not feasible'}

    dp_dist = dp_result.get('total_distance_km', 0)
    dp_time = dp_result.get('total_time_min', 0)
    dp_compute = dp_result.get('computation_time_ms', 0)

    comparison = {
        'dp': {
            'distance_km': dp_dist,
            'time_min': dp_time,
            'computation_ms': dp_compute,
            'max_detour': _max_detour(dp_result),
        }
    }

    # NN comparison
    if nn_result and nn_result.get('feasible'):
        nn_dist = nn_result.get('total_distance_km', 0)
        nn_time = nn_result.get('total_time_min', 0)
        gap_dist = ((nn_dist - dp_dist) / dp_dist * 100) if dp_dist > 0 else 0
        gap_time = ((nn_time - dp_time) / dp_time * 100) if dp_time > 0 else 0

        comparison['nearest_neighbor'] = {
            'distance_km': nn_dist,
            'time_min': nn_time,
            'computation_ms': nn_result.get('computation_time_ms', 0),
            'max_detour': _max_detour(nn_result),
            'optimality_gap_distance_pct': round(gap_dist, 1),
            'optimality_gap_time_pct': round(gap_time, 1),
        }

    # CI comparison
    if ci_result and ci_result.get('feasible'):
        ci_dist = ci_result.get('total_distance_km', 0)
        ci_time = ci_result.get('total_time_min', 0)
        gap_dist = ((ci_dist - dp_dist) / dp_dist * 100) if dp_dist > 0 else 0
        gap_time = ((ci_time - dp_time) / dp_time * 100) if dp_time > 0 else 0

        comparison['cheapest_insertion'] = {
            'distance_km': ci_dist,
            'time_min': ci_time,
            'computation_ms': ci_result.get('computation_time_ms', 0),
            'max_detour': _max_detour(ci_result),
            'optimality_gap_distance_pct': round(gap_dist, 1),
            'optimality_gap_time_pct': round(gap_time, 1),
        }

    return comparison


def _max_detour(result):
    """Get maximum detour ratio from a result."""
    metrics = result.get('rider_metrics', [])
    if not metrics:
        return 0
    return max(m.get('detour_ratio', 0) for m in metrics)
