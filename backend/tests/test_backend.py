"""Tests for the backend services and API."""
import pytest
import json
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Fresh database for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def auth_token(client, db):
    """Get a JWT token for authorized requests."""
    # Register a test user
    resp = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'test123',
        'name': 'Test User',
        'role': 'admin',
    })
    data = resp.get_json()
    return data.get('token')


# ════════════════════════════════════════════
# Graph Service Tests
# ════════════════════════════════════════════

class TestGraphService:
    """Test graph service haversine calculations."""

    def test_haversine_distance(self, app):
        from app.services.graph_service import haversine_distance
        with app.app_context():
            # Koramangala to Whitefield (~15km)
            dist = haversine_distance(12.9352, 77.6245, 12.9698, 77.7500)
            assert 12000 < dist < 16000  # 12-16 km

    def test_haversine_travel_time(self, app):
        from app.services.graph_service import haversine_travel_time
        with app.app_context():
            # Should return reasonable travel time
            time_s = haversine_travel_time(12.9352, 77.6245, 12.9698, 77.7500)
            assert time_s > 0
            # ~15km at 25km/h ≈ 36 min = 2160s, ×1.4 road factor
            assert 1500 < time_s < 4000

    def test_distance_matrix(self, app):
        from app.services.graph_service import precompute_distance_matrix
        with app.app_context():
            locations = [
                (12.9352, 77.6245),  # Koramangala
                (12.9756, 77.6068),  # MG Road
                (12.9784, 77.6408),  # Indiranagar
            ]
            time_mat, dist_mat, nodes, ms = precompute_distance_matrix(locations)
            assert time_mat.shape == (3, 3)
            assert dist_mat.shape == (3, 3)
            # Diagonal should be zero
            assert time_mat[0][0] == 0
            assert dist_mat[1][1] == 0
            # Off-diagonal should be positive
            assert time_mat[0][1] > 0
            assert dist_mat[0][2] > 0


# ════════════════════════════════════════════
# DP Optimizer Tests
# ════════════════════════════════════════════

class TestDPOptimizer:
    """Test bitmask DP optimizer."""

    def _make_riders(self, pairs):
        """Helper to create rider dicts from (pickup, dropoff) landmark pairs."""
        from app.api.demo import LANDMARKS
        riders = []
        for i, (p, d) in enumerate(pairs):
            pc = LANDMARKS[p]
            dc = LANDMARKS[d]
            riders.append({
                'pickup_lat': pc[0], 'pickup_lng': pc[1],
                'dropoff_lat': dc[0], 'dropoff_lng': dc[1],
                'pickup_address': p, 'dropoff_address': d,
                'rider_id': i + 1,
            })
        return riders

    def test_single_rider(self, app):
        """DP with 1 rider should produce a simple pickup → dropoff route."""
        from app.services.dp_optimizer import optimize
        with app.app_context():
            riders = self._make_riders([("Koramangala", "Whitefield")])
            result = optimize((12.9352, 77.6245), riders, vehicle_capacity=4)

            assert result is not None
            assert result['feasible'] is True
            assert result['algorithm'] == 'dp'
            assert len(result['route']) == 2  # pickup + dropoff
            assert result['route'][0]['type'] == 'pickup'
            assert result['route'][1]['type'] == 'dropoff'
            assert result['total_distance_km'] > 0
            assert result['total_time_min'] > 0

    def test_three_riders(self, app):
        """DP with 3 riders should find a feasible optimal route."""
        from app.services.dp_optimizer import optimize
        with app.app_context():
            riders = self._make_riders([
                ("Koramangala", "Marathahalli"),
                ("Indiranagar", "Whitefield"),
                ("HSR Layout", "Marathahalli"),
            ])
            result = optimize((12.9352, 77.6245), riders, vehicle_capacity=4)

            assert result is not None
            assert result['feasible'] is True
            assert len(result['route']) == 6  # 3 pickups + 3 dropoffs
            assert result['total_distance_km'] > 0
            assert len(result['rider_metrics']) == 3

            # All riders should have positive distances
            for rm in result['rider_metrics']:
                assert rm['direct_distance_km'] > 0
                assert rm['actual_distance_km'] > 0
                assert rm['detour_ratio'] > 0

    def test_dp_better_than_greedy(self, app):
        """DP should produce equal or better route than greedy."""
        from app.services.dp_optimizer import optimize
        from app.services.greedy_optimizer import nearest_neighbor, cheapest_insertion
        with app.app_context():
            driver = (12.9352, 77.6245)
            riders = self._make_riders([
                ("Koramangala", "Marathahalli"),
                ("Indiranagar", "Whitefield"),
                ("HSR Layout", "Marathahalli"),
            ])

            dp = optimize(driver, riders, 4)
            nn = nearest_neighbor(driver, riders, 4)
            ci = cheapest_insertion(driver, riders, 4)

            assert dp['feasible']
            assert nn['feasible']
            assert ci['feasible']
            # DP should be <= greedy (within floating point)
            assert dp['total_distance_km'] <= nn['total_distance_km'] + 0.1
            assert dp['total_distance_km'] <= ci['total_distance_km'] + 0.1

    def test_steps_tracking(self, app):
        """DP should return algorithm execution steps."""
        from app.services.dp_optimizer import optimize
        with app.app_context():
            riders = self._make_riders([("Koramangala", "Whitefield")])
            result = optimize((12.9352, 77.6245), riders)

            assert 'steps' in result
            phases = [s['phase'] for s in result['steps']]
            assert 'graph_lookup' in phases
            assert 'distance_matrix' in phases
            assert 'dp_execution' in phases
            assert 'complete' in phases

    def test_too_many_riders_returns_none(self, app):
        """DP should return None for > 8 riders."""
        from app.services.dp_optimizer import optimize
        with app.app_context():
            riders = self._make_riders([("Koramangala", "Whitefield")] * 9)
            result = optimize((12.9352, 77.6245), riders)
            assert result is None


# ════════════════════════════════════════════
# Fare Service Tests
# ════════════════════════════════════════════

class TestFareService:
    """Test fare calculation and Shapley values."""

    def test_solo_fare(self, app):
        from app.services.fare_service import calculate_solo_fare
        with app.app_context():
            fare = calculate_solo_fare(10.0, 20.0)  # 10km, 20min
            # 30 + 12*10 + 2*20 = 30 + 120 + 40 = 190
            assert fare == 190.0

    def test_solo_fare_with_surge(self, app):
        from app.services.fare_service import calculate_solo_fare
        with app.app_context():
            fare = calculate_solo_fare(10.0, 20.0, surge=1.5)
            assert fare == 285.0  # 190 × 1.5

    def test_shared_fare_less_than_solo(self, app):
        from app.services.fare_service import calculate_shared_fares
        from app.services.dp_optimizer import optimize
        from app.api.demo import LANDMARKS
        with app.app_context():
            riders = [
                {'pickup_lat': LANDMARKS['Koramangala'][0], 'pickup_lng': LANDMARKS['Koramangala'][1],
                 'dropoff_lat': LANDMARKS['Marathahalli'][0], 'dropoff_lng': LANDMARKS['Marathahalli'][1],
                 'rider_id': 1},
                {'pickup_lat': LANDMARKS['Indiranagar'][0], 'pickup_lng': LANDMARKS['Indiranagar'][1],
                 'dropoff_lat': LANDMARKS['Whitefield'][0], 'dropoff_lng': LANDMARKS['Whitefield'][1],
                 'rider_id': 2},
            ]
            result = optimize(LANDMARKS['Koramangala'], riders)
            if result and result['feasible']:
                fares = calculate_shared_fares(riders, result)
                for f in fares:
                    assert f['fare_amount'] <= f['solo_fare']
                    assert f['savings_pct'] >= 0


# ════════════════════════════════════════════
# Surge Service Tests
# ════════════════════════════════════════════

class TestSurgeService:
    """Test surge pricing logic."""

    def test_surge_tiers(self, app):
        from app.services.surge_service import _compute_surge
        with app.app_context():
            # Normal: few requests, many drivers
            s = _compute_surge(2, 5)
            assert s['surge_multiplier'] == 1.0
            assert s['tier'] == 'normal'

            # Slightly busy
            s = _compute_surge(5, 3)
            assert s['surge_multiplier'] == 1.2

            # Busy
            s = _compute_surge(8, 3)
            assert s['surge_multiplier'] == 1.5

            # Very busy
            s = _compute_surge(10, 2)
            assert s['surge_multiplier'] == 2.0
            assert s['color'] == '#ef4444'


# ════════════════════════════════════════════
# Carbon Service Tests
# ════════════════════════════════════════════

class TestCarbonService:
    """Test CO₂ emission calculations."""

    def test_carbon_savings(self, app):
        from app.services.carbon_service import calculate_carbon_savings
        with app.app_context():
            riders_metrics = [
                {'direct_distance_km': 15.0},
                {'direct_distance_km': 18.0},
                {'direct_distance_km': 12.0},
            ]
            # Solo total = 45 km, shared = 32 km → saved 13 km
            result = calculate_carbon_savings(riders_metrics, 32.0)

            assert result['solo_total_km'] == 45.0
            assert result['shared_km'] == 32.0
            assert result['km_saved'] == 13.0
            assert abs(result['co2_saved_kg'] - 2.73) < 0.01  # 13 × 0.21
            assert result['riders_count'] == 3


# ════════════════════════════════════════════
# API Tests
# ════════════════════════════════════════════

class TestAPI:
    """Test REST API endpoints."""

    def test_health(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'healthy'

    def test_demo_scenarios(self, client):
        resp = client.get('/api/demo/scenarios')
        assert resp.status_code == 200
        data = resp.get_json()
        assert '3_rider_corridor' in data['scenarios']
        assert '5_rider_spread' in data['scenarios']
        assert 'landmarks' in data

    def test_auth_flow(self, client, db):
        # Register
        resp = client.post('/api/auth/register', json={
            'email': 'authtest@example.com',
            'password': 'test123',
            'name': 'Auth Test',
            'role': 'rider',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'token' in data

        # Login
        resp = client.post('/api/auth/login', json={
            'email': 'authtest@example.com',
            'password': 'test123',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'token' in data
        token = data['token']

        # Me
        resp = client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['email'] == 'authtest@example.com'

    def test_comparison_api(self, client, auth_token):
        """Test the key comparison endpoint."""
        resp = client.post('/api/analytics/compare',
            json={
                'driver_start': {'lat': 12.9352, 'lng': 77.6245},
                'riders': [
                    {
                        'pickup_lat': 12.9352, 'pickup_lng': 77.6245,
                        'dropoff_lat': 12.9591, 'dropoff_lng': 77.6974,
                        'pickup_address': 'Koramangala', 'dropoff_address': 'Marathahalli',
                        'rider_id': 1,
                    },
                    {
                        'pickup_lat': 12.9784, 'pickup_lng': 77.6408,
                        'dropoff_lat': 12.9698, 'dropoff_lng': 77.7500,
                        'pickup_address': 'Indiranagar', 'dropoff_address': 'Whitefield',
                        'rider_id': 2,
                    },
                ],
                'vehicle_capacity': 4,
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # All three algorithms should be present
        assert 'dp' in data
        assert 'nearest_neighbor' in data
        assert 'cheapest_insertion' in data

        # DP should be feasible
        assert data['dp']['feasible'] is True
        assert data['dp']['total_distance_km'] > 0

        # Comparison metrics
        assert 'comparison' in data
        assert 'fares' in data
        assert 'carbon_savings' in data

    def test_demo_seed(self, client, db):
        resp = client.post('/api/demo/seed')
        assert resp.status_code == 201
        data = resp.get_json()
        assert len(data['accounts']) == 3
