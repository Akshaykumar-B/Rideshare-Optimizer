"""Matching engine — batch rider-driver assignment using Hungarian algorithm.

In-process matching (no Celery dependency):
1. Collects all pending ride requests
2. Finds candidate drivers within radius
3. Computes cost matrix (insertion cost for each rider-driver pair)
4. Runs Hungarian algorithm for globally optimal assignment
5. Creates/updates trips and notifies participants
"""
import logging
import time
from datetime import datetime, timezone
from scipy.optimize import linear_sum_assignment
import numpy as np

from ..extensions import db
from ..models.ride_request import RideRequest
from ..models.user import DriverProfile, User
from ..models.trip import Trip, TripRider
from ..services import graph_service
from ..services import dp_optimizer

logger = logging.getLogger(__name__)

INF_COST = 1e9


class MatchingEngine:
    """Batch matching engine using Hungarian algorithm."""

    def __init__(self, max_radius_km=5.0, max_detour_ratio=1.5):
        self.max_radius_km = max_radius_km
        self.max_detour_ratio = max_detour_ratio

    def run_batch(self):
        """Run a single batch matching cycle.

        Returns:
            dict with matching results
        """
        start = time.time()

        # 1. Collect pending requests
        pending = RideRequest.query.filter_by(status='pending').all()
        if not pending:
            return {'matches': 0, 'message': 'No pending requests'}

        # 2. Find available drivers
        available_drivers = DriverProfile.query.filter_by(is_available=True).all()
        if not available_drivers:
            return {'matches': 0, 'message': 'No available drivers'}

        n_riders = len(pending)
        n_drivers = len(available_drivers)
        m = max(n_riders, n_drivers)

        # 3. Build cost matrix
        cost_matrix = np.full((m, m), INF_COST)

        for i, request in enumerate(pending):
            for j, driver in enumerate(available_drivers):
                if driver.current_lat is None or driver.current_lng is None:
                    continue

                # Compute pickup distance
                pickup_dist = graph_service.haversine_distance(
                    driver.current_lat, driver.current_lng,
                    request.pickup_lat, request.pickup_lng
                ) / 1000  # km

                if pickup_dist > self.max_radius_km:
                    continue

                # Cost = pickup distance + route distance
                route_dist = graph_service.haversine_road_distance(
                    request.pickup_lat, request.pickup_lng,
                    request.dropoff_lat, request.dropoff_lng
                ) / 1000

                cost_matrix[i][j] = pickup_dist + route_dist * 0.5

        # 4. Run Hungarian algorithm
        try:
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
        except Exception as e:
            logger.error(f"Hungarian algorithm failed: {e}")
            return {'matches': 0, 'error': str(e)}

        # 5. Create matches
        matches = 0
        match_results = []

        for r_idx, d_idx in zip(row_ind, col_ind):
            if r_idx >= n_riders or d_idx >= n_drivers:
                continue
            if cost_matrix[r_idx][d_idx] >= INF_COST:
                continue

            request = pending[r_idx]
            driver = available_drivers[d_idx]

            # Create trip
            trip = Trip(
                driver_id=driver.id,
                status='active',
                algorithm_used='dp',
                surge_multiplier=1.0,
            )
            db.session.add(trip)
            db.session.flush()  # Get trip ID

            # Create trip rider
            direct_dist = graph_service.haversine_road_distance(
                request.pickup_lat, request.pickup_lng,
                request.dropoff_lat, request.dropoff_lng
            ) / 1000

            trip_rider = TripRider(
                trip_id=trip.id,
                ride_request_id=request.id,
                direct_distance_km=round(direct_dist, 2),
                fare_amount=0,  # Calculated later
            )
            db.session.add(trip_rider)

            # Update request status
            request.status = 'matched'

            # Build route
            driver_start = (driver.current_lat, driver.current_lng)
            rider_data = [{
                'pickup_lat': request.pickup_lat,
                'pickup_lng': request.pickup_lng,
                'dropoff_lat': request.dropoff_lat,
                'dropoff_lng': request.dropoff_lng,
                'rider_id': request.rider_id,
                'pickup_address': request.pickup_address,
                'dropoff_address': request.dropoff_address,
            }]

            result = dp_optimizer.optimize(driver_start, rider_data, driver.vehicle_capacity)
            if result and result.get('feasible'):
                trip.route_sequence = result['route']
                trip.total_distance_km = result['total_distance_km']
                trip.total_time_min = result['total_time_min']

            matches += 1
            match_results.append({
                'rider_id': request.rider_id,
                'driver_id': driver.user_id,
                'trip_id': trip.id,
                'cost': round(cost_matrix[r_idx][d_idx], 2),
            })

        db.session.commit()

        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"Batch matching: {matches} matches in {elapsed_ms:.0f}ms")

        return {
            'matches': matches,
            'pending_processed': n_riders,
            'drivers_available': n_drivers,
            'match_results': match_results,
            'computation_ms': round(elapsed_ms),
        }
