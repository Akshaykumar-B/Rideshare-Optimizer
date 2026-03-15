"""Fare service — proportional split + Shapley value fairness.

Fare model:
  base_fare = BASE_FARE + RATE_PER_KM * distance + RATE_PER_MIN * time
  shared_fare = base_fare * (1 - SHARED_DISCOUNT)
  per_rider = shared_fare * (rider_direct_dist / sum_all_direct_dists)

Shapley values: exact for n ≤ 4 (all 2^n subsets), Monte Carlo for n > 4.
"""
import time
import logging
import random
from itertools import permutations
from flask import current_app
from . import dp_optimizer

logger = logging.getLogger(__name__)


def calculate_solo_fare(distance_km, time_min, surge=1.0):
    """Calculate fare for a single solo rider."""
    base = current_app.config.get('BASE_FARE', 30.0)
    rate_km = current_app.config.get('RATE_PER_KM', 12.0)
    rate_min = current_app.config.get('RATE_PER_MIN', 2.0)
    fare = base + rate_km * distance_km + rate_min * time_min
    return round(fare * surge, 2)


def calculate_shared_fares(riders, dp_result, surge=1.0):
    """Calculate per-rider fares for a shared ride.

    Uses proportional-to-direct-distance split with shared discount.
    Ensures no rider pays more than their solo fare.

    Args:
        riders: list of rider dicts
        dp_result: result from dp_optimizer.optimize()
        surge: surge multiplier

    Returns:
        list of fare dicts per rider
    """
    n = len(riders)
    if n == 0:
        return []

    discount = current_app.config.get('SHARED_DISCOUNT', 0.30)
    rider_metrics = dp_result.get('rider_metrics', [])
    total_dist_km = dp_result.get('total_distance_km', 0)
    total_time_min = dp_result.get('total_time_min', 0)

    # Total route fare (before discount)
    total_fare = calculate_solo_fare(total_dist_km, total_time_min, surge)

    # Shared fare (with discount)
    shared_fare = total_fare * (1 - discount)

    # Solo fares for each rider
    solo_fares = []
    direct_distances = []
    for rm in rider_metrics:
        solo_dist = rm['direct_distance_km']
        solo_time = rm['solo_time_min']
        solo_fares.append(calculate_solo_fare(solo_dist, solo_time, surge))
        direct_distances.append(solo_dist)

    # Proportional split
    total_direct = sum(direct_distances) if direct_distances else 1
    fares = []

    for i, rm in enumerate(rider_metrics):
        proportion = direct_distances[i] / total_direct if total_direct > 0 else 1 / n
        rider_fare = shared_fare * proportion
        # Cap at solo fare (rider should never pay more for sharing)
        rider_fare = min(rider_fare, solo_fares[i])
        fares.append({
            'rider_index': i,
            'rider_id': rm.get('rider_id'),
            'fare_amount': round(rider_fare, 2),
            'solo_fare': solo_fares[i],
            'savings_pct': round((1 - rider_fare / solo_fares[i]) * 100, 1) if solo_fares[i] > 0 else 0,
            'proportion': round(proportion, 3),
            'surge_multiplier': surge,
        })

    return fares


def calculate_shapley_values(riders, driver_start, vehicle_capacity=4, surge=1.0):
    """Calculate Shapley fare values for fair cost allocation.

    Exact computation for n ≤ 4 (16 subsets), Monte Carlo for n > 4.

    The Shapley value for rider i = average marginal contribution across
    all permutations of riders.

    Returns:
        list of dicts with shapley_fare per rider
    """
    n = len(riders)
    if n == 0:
        return []

    start = time.time()

    if n <= 4:
        shapley = _exact_shapley(riders, driver_start, vehicle_capacity)
    else:
        shapley = _monte_carlo_shapley(riders, driver_start, vehicle_capacity, num_samples=200)

    computation_ms = (time.time() - start) * 1000

    # Apply surge and normalize
    total_shapley = sum(shapley)
    result = []
    for i in range(n):
        rider_shapley = shapley[i] * surge if total_shapley > 0 else 0
        result.append({
            'rider_index': i,
            'rider_id': riders[i].get('rider_id'),
            'shapley_fare': round(rider_shapley, 2),
            'shapley_proportion': round(shapley[i] / total_shapley, 3) if total_shapley > 0 else 0,
            'computation_ms': round(computation_ms),
            'method': 'exact' if n <= 4 else 'monte_carlo',
        })

    return result


def _coalition_cost(rider_subset, all_riders, driver_start, vehicle_capacity):
    """Compute optimal route cost for a subset of riders."""
    if not rider_subset:
        return 0.0

    subset_riders = [all_riders[i] for i in rider_subset]
    result = dp_optimizer.optimize(driver_start, subset_riders, vehicle_capacity)

    if result is None or not result.get('feasible', False):
        return float('inf')

    # Cost = total_distance_km (using distance as the cost metric for fairness)
    return result.get('total_distance_km', 0)


def _exact_shapley(riders, driver_start, vehicle_capacity):
    """Exact Shapley values by enumerating all 2^n coalitions."""
    n = len(riders)
    shapley = [0.0] * n
    rider_indices = list(range(n))

    # Enumerate all permutations
    from math import factorial
    total_perms = factorial(n)

    for perm in permutations(rider_indices):
        for pos, player in enumerate(perm):
            # Coalition before this player
            coalition_before = set(perm[:pos])
            coalition_with = coalition_before | {player}

            cost_without = _coalition_cost(list(coalition_before), riders, driver_start, vehicle_capacity)
            cost_with = _coalition_cost(list(coalition_with), riders, driver_start, vehicle_capacity)

            marginal = cost_with - cost_without
            shapley[player] += marginal / total_perms

    return shapley


def _monte_carlo_shapley(riders, driver_start, vehicle_capacity, num_samples=200):
    """Monte Carlo approximation of Shapley values."""
    n = len(riders)
    shapley = [0.0] * n
    rider_indices = list(range(n))

    for _ in range(num_samples):
        perm = rider_indices[:]
        random.shuffle(perm)

        for pos, player in enumerate(perm):
            coalition_before = set(perm[:pos])
            coalition_with = coalition_before | {player}

            cost_without = _coalition_cost(list(coalition_before), riders, driver_start, vehicle_capacity)
            cost_with = _coalition_cost(list(coalition_with), riders, driver_start, vehicle_capacity)

            marginal = cost_with - cost_without
            shapley[player] += marginal / num_samples

    return shapley
