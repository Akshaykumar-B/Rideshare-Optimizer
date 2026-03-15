"""Demo API — pre-seeded scenarios for demo day."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models.user import User, DriverProfile
from ..models.ride_request import RideRequest
from ..models.trip import Trip, TripRider

demo_bp = Blueprint('demo', __name__)

# Bangalore landmarks with real coordinates
LANDMARKS = {
    "Koramangala":      (12.9352, 77.6245),
    "Whitefield":       (12.9698, 77.7500),
    "MG Road":          (12.9756, 77.6068),
    "Electronic City":  (12.8399, 77.6770),
    "Indiranagar":      (12.9784, 77.6408),
    "HSR Layout":       (12.9116, 77.6474),
    "Jayanagar":        (12.9299, 77.5838),
    "Marathahalli":     (12.9591, 77.6974),
    "Yelahanka":        (13.1007, 77.5963),
    "Banashankari":     (12.9255, 77.5468),
    "JP Nagar":         (12.9063, 77.5857),
    "Hebbal":           (13.0358, 77.5970),
}

DEMO_SCENARIOS = {
    "3_rider_corridor": {
        "name": "3-Rider Corridor (Koramangala → Whitefield)",
        "description": "3 riders heading along the Koramangala → Whitefield corridor. Good for showing basic DP optimization.",
        "driver_start": "Koramangala",
        "riders": [
            {"pickup": "Koramangala", "dropoff": "Marathahalli", "name": "Rider A"},
            {"pickup": "Indiranagar", "dropoff": "Whitefield", "name": "Rider B"},
            {"pickup": "HSR Layout", "dropoff": "Marathahalli", "name": "Rider C"},
        ],
    },
    "4_rider_cross": {
        "name": "4-Rider Cross-City",
        "description": "4 riders across different city zones. Shows moderate DP complexity (256 states).",
        "driver_start": "MG Road",
        "riders": [
            {"pickup": "MG Road", "dropoff": "Electronic City", "name": "Rider A"},
            {"pickup": "Jayanagar", "dropoff": "Whitefield", "name": "Rider B"},
            {"pickup": "Koramangala", "dropoff": "Hebbal", "name": "Rider C"},
            {"pickup": "Indiranagar", "dropoff": "JP Nagar", "name": "Rider D"},
        ],
    },
    "5_rider_spread": {
        "name": "5-Rider City-Wide Spread",
        "description": "5 riders spread across Bangalore. Shows clear DP vs greedy gap (1024 states).",
        "driver_start": "MG Road",
        "riders": [
            {"pickup": "MG Road", "dropoff": "Electronic City", "name": "Rider A"},
            {"pickup": "Jayanagar", "dropoff": "Whitefield", "name": "Rider B"},
            {"pickup": "Indiranagar", "dropoff": "Banashankari", "name": "Rider C"},
            {"pickup": "Koramangala", "dropoff": "Hebbal", "name": "Rider D"},
            {"pickup": "HSR Layout", "dropoff": "Yelahanka", "name": "Rider E"},
        ],
    },
    "7_rider_max": {
        "name": "7-Rider Maximum DP",
        "description": "7 riders — maximum DP capacity (16,384 states). Shows computation time and full optimization.",
        "driver_start": "Hebbal",
        "riders": [
            {"pickup": "Hebbal", "dropoff": "Electronic City", "name": "Rider A"},
            {"pickup": "Yelahanka", "dropoff": "JP Nagar", "name": "Rider B"},
            {"pickup": "MG Road", "dropoff": "Banashankari", "name": "Rider C"},
            {"pickup": "Indiranagar", "dropoff": "Jayanagar", "name": "Rider D"},
            {"pickup": "Koramangala", "dropoff": "Whitefield", "name": "Rider E"},
            {"pickup": "Marathahalli", "dropoff": "HSR Layout", "name": "Rider F"},
            {"pickup": "HSR Layout", "dropoff": "Yelahanka", "name": "Rider G"},
        ],
    },
}


@demo_bp.route('/scenarios', methods=['GET'])
def list_scenarios():
    """List available demo scenarios."""
    scenarios = {}
    for key, sc in DEMO_SCENARIOS.items():
        scenarios[key] = {
            'name': sc['name'],
            'description': sc['description'],
            'rider_count': len(sc['riders']),
            'driver_start': sc['driver_start'],
        }
    return jsonify({'scenarios': scenarios, 'landmarks': LANDMARKS}), 200


@demo_bp.route('/load', methods=['POST'])
@jwt_required()
def load_scenario():
    """Load a pre-defined demo scenario for the comparison page.

    Query param: scenario (e.g., "5_rider_spread")

    Returns the scenario data formatted for the comparison API.
    """
    data = request.get_json() or {}
    scenario_key = data.get('scenario', request.args.get('scenario', '3_rider_corridor'))

    if scenario_key not in DEMO_SCENARIOS:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': f'Unknown scenario. Available: {list(DEMO_SCENARIOS.keys())}'
        }), 400

    sc = DEMO_SCENARIOS[scenario_key]
    driver_coords = LANDMARKS[sc['driver_start']]

    riders = []
    for i, r in enumerate(sc['riders']):
        pickup = LANDMARKS[r['pickup']]
        dropoff = LANDMARKS[r['dropoff']]
        riders.append({
            'pickup_lat': pickup[0],
            'pickup_lng': pickup[1],
            'dropoff_lat': dropoff[0],
            'dropoff_lng': dropoff[1],
            'pickup_address': r['pickup'],
            'dropoff_address': r['dropoff'],
            'rider_id': i + 1,
            'name': r.get('name', f'Rider {i + 1}'),
        })

    return jsonify({
        'scenario': scenario_key,
        'name': sc['name'],
        'description': sc['description'],
        'driver_start': {
            'lat': driver_coords[0],
            'lng': driver_coords[1],
            'address': sc['driver_start'],
        },
        'riders': riders,
        'vehicle_capacity': 4,
    }), 200


@demo_bp.route('/seed', methods=['POST'])
def seed_demo_data():
    """Seed demo accounts and data. For initial setup only."""
    # Create demo users
    accounts = [
        {'email': 'rider@demo.com', 'name': 'Demo Rider', 'role': 'rider', 'password': 'demo123'},
        {'email': 'driver@demo.com', 'name': 'Demo Driver', 'role': 'driver', 'password': 'demo123'},
        {'email': 'admin@demo.com', 'name': 'Demo Admin', 'role': 'admin', 'password': 'demo123'},
        {'email': 'akshaykumarbandam@gmail.com', 'name': 'Akshay Kumar', 'role': 'admin', 'password': 'demo123'},
    ]

    created = []
    for acct in accounts:
        existing = User.query.filter_by(email=acct['email']).first()
        if existing:
            created.append({'email': acct['email'], 'status': 'already_exists'})
            continue

        user = User(email=acct['email'], name=acct['name'], role=acct['role'])
        user.set_password(acct['password'])
        db.session.add(user)
        db.session.flush()

        if acct['role'] == 'driver':
            profile = DriverProfile(
                user_id=user.id,
                vehicle_capacity=4,
                is_available=True,
                current_lat=LANDMARKS['Koramangala'][0],
                current_lng=LANDMARKS['Koramangala'][1],
            )
            db.session.add(profile)

        created.append({'email': acct['email'], 'status': 'created', 'id': user.id})

    db.session.commit()
    return jsonify({
        'message': 'Demo data seeded',
        'accounts': created,
        'login_hint': 'Use email/password from the accounts above. Password: demo123',
    }), 201


@demo_bp.route('/reset', methods=['POST'])
def reset_demo():
    """Reset all demo data. Caution: deletes all trips and ride requests."""
    TripRider.query.delete()
    Trip.query.delete()
    RideRequest.query.delete()
    db.session.commit()

    return jsonify({'message': 'Demo data reset. Run /api/demo/seed to re-seed.'}), 200
