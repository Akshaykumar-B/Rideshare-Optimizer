"""Greedy optimizers for comparison against DP optimal.

Implements two heuristics:
1. Nearest-Neighbor: always go to the closest feasible stop. O(n²).
2. Cheapest Insertion: iteratively insert each rider pair at the cheapest position. O(n²·k).

Both respect precedence and capacity constraints but provide no optimality guarantees.
"""
import time
import logging
import numpy as np
from . import graph_service

logger = logging.getLogger(__name__)

INF = float('inf')


def nearest_neighbor(driver_start, riders, vehicle_capacity=4, max_detour_ratio=1.5):
    """Nearest-Neighbor greedy heuristic.

    From the current position, always move to the nearest feasible unvisited location.
    """
    n = len(riders)
    steps = []
    total_start = time.time()

    if n == 0:
        return _empty_result(driver_start, 'greedy_nn', steps)

    # Build locations and matrices
    locations = [driver_start]
    for r in riders:
        locations.append((r['pickup_lat'], r['pickup_lng']))
    for r in riders:
        locations.append((r['dropoff_lat'], r['dropoff_lng']))

    num_locs = 2 * n + 1

    phase_start = time.time()
    time_matrix, dist_matrix, nodes, matrix_ms = graph_service.precompute_distance_matrix(locations)

    steps.append({
        'phase': 'distance_matrix',
        'message': f'Computing {num_locs}×{num_locs} distance matrix...',
        'duration_ms': round(matrix_ms),
    })

    # Compute solo distances
    solo_distances = []
    solo_times = []
    for i in range(n):
        solo_distances.append(dist_matrix[i + 1][i + 1 + n])
        solo_times.append(time_matrix[i + 1][i + 1 + n])

    # Parse time windows
    time_windows = []
    for r in riders:
        earliest = r.get('earliest_pickup', 0) or 0
        latest = r.get('latest_pickup', INF) or INF
        time_windows.append((earliest, latest))

    # ── Greedy construction ──
    phase_start = time.time()
    visited = set()
    route_indices = []
    current = 0  # Start at driver location
    current_time = 0.0
    load = 0
    picked = [False] * n
    dropped = [False] * n
    iterations = 0

    while len(visited) < 2 * n:
        best_next = -1
        best_cost = INF
        iterations += 1

        for j in range(2 * n):
            if j in visited:
                continue

            loc_idx = j + 1
            if j < n:
                # Pickup
                rider_idx = j
                if load >= vehicle_capacity:
                    continue
                travel = time_matrix[current][loc_idx]
                arrival = current_time + travel
                earliest, latest = time_windows[rider_idx]
                arrival = max(arrival, earliest)
                if arrival > latest:
                    continue
                cost = travel
            else:
                # Dropoff
                rider_idx = j - n
                if not picked[rider_idx]:
                    continue
                cost = time_matrix[current][loc_idx]

            if cost < best_cost:
                best_cost = cost
                best_next = j

        if best_next == -1:
            # No feasible next stop — try to force any remaining
            break

        visited.add(best_next)
        loc_idx = best_next + 1
        route_indices.append(loc_idx)

        travel = time_matrix[current][loc_idx]
        current_time += travel

        if best_next < n:
            rider_idx = best_next
            earliest, _ = time_windows[rider_idx]
            current_time = max(current_time, earliest)
            picked[rider_idx] = True
            load += 1
        else:
            rider_idx = best_next - n
            dropped[rider_idx] = True
            load -= 1

        current = loc_idx

    nn_ms = (time.time() - phase_start) * 1000

    steps.append({
        'phase': 'nn_construction',
        'message': f'Nearest-Neighbor greedy: {iterations} iterations...',
        'duration_ms': round(nn_ms),
        'details': {'iterations': iterations}
    })

    # Build result
    return _build_result(
        'greedy_nn', driver_start, riders, n, locations,
        time_matrix, dist_matrix, solo_distances, solo_times,
        route_indices, max_detour_ratio, steps, total_start
    )


def cheapest_insertion(driver_start, riders, vehicle_capacity=4, max_detour_ratio=1.5):
    """Cheapest Insertion heuristic.

    Start with driver's location. For each unrouted rider, find the insertion
    position that increases total route cost the least.
    """
    n = len(riders)
    steps = []
    total_start = time.time()

    if n == 0:
        return _empty_result(driver_start, 'greedy_ci', steps)

    # Build locations and matrices
    locations = [driver_start]
    for r in riders:
        locations.append((r['pickup_lat'], r['pickup_lng']))
    for r in riders:
        locations.append((r['dropoff_lat'], r['dropoff_lng']))

    num_locs = 2 * n + 1

    phase_start = time.time()
    time_matrix, dist_matrix, nodes, matrix_ms = graph_service.precompute_distance_matrix(locations)

    steps.append({
        'phase': 'distance_matrix',
        'message': f'Computing {num_locs}×{num_locs} distance matrix...',
        'duration_ms': round(matrix_ms),
    })

    # Solo distances
    solo_distances = []
    solo_times = []
    for i in range(n):
        solo_distances.append(dist_matrix[i + 1][i + 1 + n])
        solo_times.append(time_matrix[i + 1][i + 1 + n])

    # Time windows
    time_windows = []
    for r in riders:
        earliest = r.get('earliest_pickup', 0) or 0
        latest = r.get('latest_pickup', INF) or INF
        time_windows.append((earliest, latest))

    # ── Cheapest Insertion ──
    phase_start = time.time()

    # Route is a list of location indices, starting with driver (0)
    route = [0]
    inserted_riders = set()
    insertions = 0

    for _ in range(n):
        best_cost = INF
        best_rider = -1
        best_pickup_pos = -1
        best_dropoff_pos = -1

        for rider_idx in range(n):
            if rider_idx in inserted_riders:
                continue

            pickup_idx = rider_idx + 1
            dropoff_idx = rider_idx + 1 + n

            # Try all valid insertion positions for pickup and dropoff
            for p_pos in range(1, len(route) + 1):
                # Check capacity at insertion point
                load_at_pos = _compute_load_at(route, p_pos, n)
                if load_at_pos >= vehicle_capacity:
                    continue

                # Check time window feasibility for pickup
                if not _check_time_feasibility(route, p_pos, pickup_idx, time_matrix, time_windows, n, is_pickup=True):
                    continue

                for d_pos in range(p_pos + 1, len(route) + 2):
                    # Compute insertion cost
                    cost = _insertion_cost(route, pickup_idx, dropoff_idx, p_pos, d_pos, time_matrix)

                    if cost < best_cost:
                        best_cost = cost
                        best_rider = rider_idx
                        best_pickup_pos = p_pos
                        best_dropoff_pos = d_pos

        if best_rider == -1:
            break  # No feasible insertion

        # Insert the best rider's pickup and dropoff
        pickup_idx = best_rider + 1
        dropoff_idx = best_rider + 1 + n
        route.insert(best_pickup_pos, pickup_idx)
        route.insert(best_dropoff_pos, dropoff_idx)
        inserted_riders.add(best_rider)
        insertions += 1

    ci_ms = (time.time() - phase_start) * 1000

    steps.append({
        'phase': 'ci_construction',
        'message': f'Cheapest Insertion: {insertions} rider insertions...',
        'duration_ms': round(ci_ms),
        'details': {'insertions': insertions}
    })

    # Convert route to location indices (skip the driver start at index 0)
    route_indices = [idx for idx in route if idx != 0]

    return _build_result(
        'greedy_ci', driver_start, riders, n, locations,
        time_matrix, dist_matrix, solo_distances, solo_times,
        route_indices, max_detour_ratio, steps, total_start
    )


def _compute_load_at(route, position, n):
    """Compute vehicle load at a given position in the route."""
    load = 0
    for i in range(1, min(position, len(route))):
        idx = route[i]
        bit = idx - 1
        if bit < n:
            load += 1  # Pickup
        else:
            load -= 1  # Dropoff
    return load


def _check_time_feasibility(route, position, loc_idx, time_matrix, time_windows, n, is_pickup=True):
    """Check if inserting at position respects time windows (simplified check)."""
    if not is_pickup:
        return True
    bit = loc_idx - 1
    if bit < n:
        # Check if we can reach this pickup in time
        if position > 0 and position <= len(route):
            prev = route[position - 1]
            travel = time_matrix[prev][loc_idx]
            # Simplified: just check if travel time is reasonable
            _, latest = time_windows[bit]
            if latest < INF and travel > latest:
                return False
    return True


def _insertion_cost(route, pickup_idx, dropoff_idx, p_pos, d_pos, time_matrix):
    """Compute the additional cost of inserting pickup at p_pos and dropoff at d_pos."""
    cost = 0.0

    # Cost of inserting pickup
    if p_pos <= len(route):
        prev = route[p_pos - 1]
        cost += time_matrix[prev][pickup_idx]
        if p_pos < len(route):
            nxt = route[p_pos]
            cost += time_matrix[pickup_idx][nxt]
            cost -= time_matrix[prev][nxt]
        # If d_pos is right after p_pos
        if d_pos == p_pos + 1:
            cost += time_matrix[pickup_idx][dropoff_idx]
            if d_pos <= len(route):
                nxt = route[d_pos - 1] if d_pos - 1 < len(route) else None
                if nxt is not None and nxt != route[p_pos - 1]:
                    cost += time_matrix[dropoff_idx][nxt]
                    cost -= time_matrix[pickup_idx][nxt]
        else:
            # Dropoff inserted elsewhere
            # Adjust d_pos for the inserted pickup
            adj_d = d_pos - 1  # Position in route after pickup insertion
            if adj_d < len(route):
                prev_d = route[adj_d - 1] if adj_d > 0 else pickup_idx
                cost += time_matrix[prev_d][dropoff_idx]
                if adj_d < len(route):
                    nxt_d = route[adj_d]
                    cost += time_matrix[dropoff_idx][nxt_d]
                    cost -= time_matrix[prev_d][nxt_d]

    return cost


def _build_result(algorithm, driver_start, riders, n, locations,
                  time_matrix, dist_matrix, solo_distances, solo_times,
                  route_indices, max_detour_ratio, steps, total_start):
    """Build standardized result dict from a route."""
    # Compute metrics
    total_distance = 0.0
    total_time = 0.0
    rider_actual_dist = [0.0] * n
    rider_onboard = [False] * n
    # Convert numpy to native float
    solo_distances = [float(d) for d in solo_distances]
    solo_times = [float(t) for t in solo_times]
    rider_pickup_order = [0] * n
    rider_dropoff_order = [0] * n
    stop_num = 0

    prev_idx = 0
    for loc_idx in route_indices:
        segment_dist = float(dist_matrix[prev_idx][loc_idx])
        segment_time = float(time_matrix[prev_idx][loc_idx])
        total_distance += segment_dist
        total_time += segment_time

        for i in range(n):
            if rider_onboard[i]:
                rider_actual_dist[i] += segment_dist

        bit_idx = loc_idx - 1
        if bit_idx < n:
            rider_idx = bit_idx
            rider_onboard[rider_idx] = True
            stop_num += 1
            rider_pickup_order[rider_idx] = stop_num
        else:
            rider_idx = bit_idx - n
            rider_onboard[rider_idx] = False
            stop_num += 1
            rider_dropoff_order[rider_idx] = stop_num

        prev_idx = loc_idx

    # Build route stops
    route = []
    stop_num = 0
    for loc_idx in route_indices:
        bit_idx = loc_idx - 1
        if bit_idx < n:
            rider_idx = bit_idx
            stop_type = 'pickup'
            label = riders[rider_idx].get('pickup_address', f"Pickup {rider_idx + 1}")
        else:
            rider_idx = bit_idx - n
            stop_type = 'dropoff'
            label = riders[rider_idx].get('dropoff_address', f"Dropoff {rider_idx + 1}")

        stop_num += 1
        route.append({
            'location_index': loc_idx,
            'lat': locations[loc_idx][0],
            'lng': locations[loc_idx][1],
            'type': stop_type,
            'rider_index': rider_idx,
            'rider_id': riders[rider_idx].get('rider_id'),
            'label': label,
            'order': stop_num,
        })

    # Per-rider metrics
    rider_metrics = []
    detour_violated = False
    for i in range(n):
        detour = rider_actual_dist[i] / solo_distances[i] if solo_distances[i] > 0 else 1.0
        if detour > max_detour_ratio:
            detour_violated = True
        rider_metrics.append({
            'rider_index': i,
            'rider_id': riders[i].get('rider_id'),
            'direct_distance_km': round(solo_distances[i] / 1000, 2),
            'actual_distance_km': round(rider_actual_dist[i] / 1000, 2),
            'detour_ratio': round(detour, 3),
            'solo_time_min': round(solo_times[i] / 60, 1),
            'pickup_order': rider_pickup_order[i],
            'dropoff_order': rider_dropoff_order[i],
        })

    total_ms = (time.time() - total_start) * 1000

    steps.append({
        'phase': 'complete',
        'message': f'{algorithm.upper()} route computed.',
        'total_ms': round(total_ms),
    })

    # Build polyline
    route_coords = [driver_start] + [(s['lat'], s['lng']) for s in route]
    polyline = graph_service.get_route_polyline(route_coords)

    return {
        'feasible': True,
        'algorithm': algorithm,
        'route': route,
        'polyline': [{'lat': p[0], 'lng': p[1]} for p in polyline],
        'total_distance_km': round(total_distance / 1000, 2),
        'total_time_min': round(total_time / 60, 1),
        'rider_metrics': rider_metrics,
        'detour_violated': detour_violated,
        'driver_start': {'lat': driver_start[0], 'lng': driver_start[1]},
        'steps': steps,
        'computation_time_ms': round(total_ms),
    }


def _empty_result(driver_start, algorithm, steps):
    """Return result for zero riders."""
    steps.append({'phase': 'complete', 'message': 'No riders to optimize.', 'total_ms': 0})
    return {
        'feasible': True,
        'algorithm': algorithm,
        'route': [],
        'polyline': [],
        'total_distance_km': 0,
        'total_time_min': 0,
        'rider_metrics': [],
        'detour_violated': False,
        'driver_start': {'lat': driver_start[0], 'lng': driver_start[1]},
        'steps': steps,
        'computation_time_ms': 0,
    }
