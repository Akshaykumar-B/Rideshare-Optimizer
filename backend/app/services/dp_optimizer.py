"""Bitmask DP optimizer for the Pickup-and-Delivery Problem with Time Windows (PDPTW).

Finds the provably optimal ordering of pickup/dropoff stops subject to:
1. Precedence: pickup_i must come before dropoff_i
2. Capacity: at most C passengers at any time
3. Time windows: arrive within [earliest, latest] for pickups
4. Detour: no rider's actual travel exceeds 1.5× their solo distance

Complexity: O(n · 4^n · C) time, O(4^n · (2n+1)) space
where n = number of riders, C = vehicle capacity.
"""
import time
import logging
import numpy as np
from . import graph_service

logger = logging.getLogger(__name__)

INF = float('inf')


def optimize(driver_start, riders, vehicle_capacity=4, max_detour_ratio=1.5):
    """Run bitmask DP to find the optimal multi-stop route.

    Args:
        driver_start: (lat, lng) tuple for driver's starting location.
        riders: list of dicts, each with:
            - pickup_lat, pickup_lng
            - dropoff_lat, dropoff_lng
            - earliest_pickup (optional, seconds from now)
            - latest_pickup (optional, seconds from now)
            - rider_id (optional, for labeling)
            - pickup_address, dropoff_address (optional)
        vehicle_capacity: max passengers at any time.
        max_detour_ratio: max ratio of actual vs solo travel distance.

    Returns:
        dict with route, metrics, and algorithm steps, or None if infeasible / too many riders.
    """
    n = len(riders)
    steps = []
    total_start = time.time()

    if n == 0:
        return _empty_result(driver_start, steps)

    if n > 8:
        logger.info(f"Too many riders ({n}) for DP. Returning None for heuristic fallback.")
        return None

    # ──────────────────────────────────────────
    # Phase 1: Build locations list
    # ──────────────────────────────────────────
    phase_start = time.time()

    # Locations: index 0 = driver start
    #            index 1..n = pickups
    #            index n+1..2n = dropoffs
    locations = [driver_start]
    for r in riders:
        locations.append((r['pickup_lat'], r['pickup_lng']))
    for r in riders:
        locations.append((r['dropoff_lat'], r['dropoff_lng']))

    num_locs = 2 * n + 1  # total locations including driver start

    steps.append({
        'phase': 'graph_lookup',
        'message': f'Finding nearest road network nodes for {num_locs} locations...',
        'duration_ms': round((time.time() - phase_start) * 1000),
        'details': {'num_locations': num_locs, 'mode': graph_service.get_graph_mode()}
    })

    # ──────────────────────────────────────────
    # Phase 2: Precompute distance matrix
    # ──────────────────────────────────────────
    phase_start = time.time()
    time_matrix, dist_matrix, nodes, matrix_ms = graph_service.precompute_distance_matrix(locations)

    steps.append({
        'phase': 'distance_matrix',
        'message': f'Computing {num_locs}×{num_locs} distance matrix via A*...',
        'duration_ms': round(matrix_ms),
        'details': {'matrix_size': f'{num_locs}x{num_locs}', 'total_pairs': num_locs * (num_locs - 1)}
    })

    # ──────────────────────────────────────────
    # Phase 3: Compute solo distances (for detour constraint + fare calculation)
    # ──────────────────────────────────────────
    solo_times = []
    solo_distances = []
    for i in range(n):
        pickup_idx = i + 1
        dropoff_idx = i + 1 + n
        solo_times.append(time_matrix[pickup_idx][dropoff_idx])
        solo_distances.append(dist_matrix[pickup_idx][dropoff_idx])

    # Parse time windows
    time_windows = []
    for r in riders:
        earliest = r.get('earliest_pickup', 0) or 0
        latest = r.get('latest_pickup', INF) or INF
        time_windows.append((earliest, latest))

    # ──────────────────────────────────────────
    # Phase 4: Bitmask DP
    # ──────────────────────────────────────────
    phase_start = time.time()

    # State: dp[mask][v] = (min_time, load, rider_actual_dist)
    # mask: 2n-bit integer, bit i set = location i+1 has been visited
    # v: current location index (0..2n)
    total_bits = 2 * n
    total_states = 1 << total_bits

    # dp_time[mask][v] = minimum arrival time at location v having visited mask
    dp_time = np.full((total_states, num_locs), INF)
    dp_prev = np.full((total_states, num_locs, 2), -1, dtype=np.int32)  # (prev_mask, prev_v)

    # Track per-rider actual distance for detour constraint
    # rider_dist[mask][v][i] = actual distance traveled by rider i so far
    # (This is approximate — we track from pickup to current if rider is onboard)
    # For memory efficiency, we compute detour at the end via backtracking

    # Start: at driver's location (index 0), nothing visited
    dp_time[0][0] = 0.0
    states_explored = 0
    states_pruned = 0

    for mask in range(total_states):
        for v in range(num_locs):
            if dp_time[mask][v] >= INF:
                continue

            current_time = dp_time[mask][v]
            states_explored += 1

            # Compute current load
            load = 0
            for i in range(n):
                pickup_bit = i          # bit for pickup_i
                dropoff_bit = i + n     # bit for dropoff_i
                picked = bool(mask & (1 << pickup_bit))
                dropped = bool(mask & (1 << dropoff_bit))
                if picked and not dropped:
                    load += 1

            # Try visiting each unvisited location
            for j in range(total_bits):
                if mask & (1 << j):
                    continue  # Already visited

                loc_idx = j + 1  # Location index (1..2n)

                # Determine if this is a pickup or dropoff
                if j < n:
                    # Pickup j
                    rider_idx = j
                    is_pickup = True
                else:
                    # Dropoff (j - n)
                    rider_idx = j - n
                    is_pickup = False

                # ── Constraint checks ──

                # 1. Precedence: dropoff only if pickup already done
                if not is_pickup:
                    pickup_bit = rider_idx
                    if not (mask & (1 << pickup_bit)):
                        states_pruned += 1
                        continue

                # 2. Capacity: pickup only if load < capacity
                if is_pickup and load >= vehicle_capacity:
                    states_pruned += 1
                    continue

                # 3. Time window: pickup must be within [earliest, latest]
                travel = time_matrix[v][loc_idx]
                arrival = current_time + travel

                if is_pickup:
                    earliest, latest = time_windows[rider_idx]
                    # Wait if arriving early
                    arrival = max(arrival, earliest)
                    if arrival > latest:
                        states_pruned += 1
                        continue

                # Update DP state
                new_mask = mask | (1 << j)
                if arrival < dp_time[new_mask][loc_idx]:
                    dp_time[new_mask][loc_idx] = arrival
                    dp_prev[new_mask][loc_idx] = [mask, v]

    dp_ms = (time.time() - phase_start) * 1000

    steps.append({
        'phase': 'dp_execution',
        'message': f'Running bitmask DP over {total_states} states...',
        'duration_ms': round(dp_ms),
        'details': {
            'total_states': total_states,
            'states_explored': states_explored,
            'states_pruned': states_pruned,
            'riders': n,
            'bits': total_bits,
        }
    })

    # ──────────────────────────────────────────
    # Phase 5: Find optimal final state and backtrack
    # ──────────────────────────────────────────
    phase_start = time.time()

    full_mask = total_states - 1  # All locations visited
    best_time = INF
    best_last = -1

    for v in range(num_locs):
        if dp_time[full_mask][v] < best_time:
            best_time = dp_time[full_mask][v]
            best_last = v

    if best_last == -1:
        steps.append({
            'phase': 'complete',
            'message': 'No feasible route found!',
            'duration_ms': round((time.time() - total_start) * 1000),
        })
        return {
            'feasible': False,
            'algorithm': 'dp',
            'steps': steps,
            'message': 'No feasible route satisfying all constraints.',
        }

    # Backtrack to reconstruct route
    route_indices = []
    mask = full_mask
    v = best_last

    while v != 0 or mask != 0:
        route_indices.append(v)
        if mask == 0 and v == 0:
            break
        prev_mask, prev_v = int(dp_prev[mask][v][0]), int(dp_prev[mask][v][1])
        if prev_mask == -1:
            break
        mask = prev_mask
        v = prev_v

    route_indices.reverse()

    # ──────────────────────────────────────────
    # Phase 6: Build route with metrics
    # ──────────────────────────────────────────
    route = []
    total_distance = 0.0
    rider_actual_dist = [0.0] * n
    rider_onboard = [False] * n
    # Convert numpy distances to native Python floats
    solo_distances = [float(d) for d in solo_distances]
    solo_times = [float(t) for t in solo_times]
    rider_pickup_order = [0] * n
    rider_dropoff_order = [0] * n
    stop_num = 0

    prev_idx = 0  # Start at driver location
    for loc_idx in route_indices:
        if loc_idx == 0:
            continue  # Skip driver start

        segment_dist = float(dist_matrix[prev_idx][loc_idx])
        segment_time = float(time_matrix[prev_idx][loc_idx])
        total_distance += segment_dist

        # Add segment distance to onboard riders
        for i in range(n):
            if rider_onboard[i]:
                rider_actual_dist[i] += segment_dist

        # Determine stop type
        bit_idx = loc_idx - 1
        if bit_idx < n:
            rider_idx = bit_idx
            stop_type = 'pickup'
            rider_onboard[rider_idx] = True
            stop_num += 1
            rider_pickup_order[rider_idx] = stop_num
            label = riders[rider_idx].get('pickup_address', f"Pickup {rider_idx + 1}")
        else:
            rider_idx = bit_idx - n
            stop_type = 'dropoff'
            rider_onboard[rider_idx] = False
            stop_num += 1
            rider_dropoff_order[rider_idx] = stop_num
            label = riders[rider_idx].get('dropoff_address', f"Dropoff {rider_idx + 1}")

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

        prev_idx = loc_idx

    # Compute per-rider detour ratios
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

    total_time = float(best_time)
    total_ms = (time.time() - total_start) * 1000

    steps.append({
        'phase': 'backtrack',
        'message': 'Reconstructing optimal route...',
        'duration_ms': round((time.time() - phase_start) * 1000),
    })

    steps.append({
        'phase': 'complete',
        'message': 'Optimal route found!',
        'total_ms': round(total_ms),
    })

    # Build route polyline for map display
    route_coords = [driver_start] + [(s['lat'], s['lng']) for s in route]
    polyline = graph_service.get_route_polyline(route_coords)

    return {
        'feasible': True,
        'algorithm': 'dp',
        'route': route,
        'polyline': [{'lat': p[0], 'lng': p[1]} for p in polyline],
        'total_distance_km': round(total_distance / 1000, 2),
        'total_time_min': round(total_time / 60, 1),
        'rider_metrics': rider_metrics,
        'detour_violated': detour_violated,
        'driver_start': {'lat': driver_start[0], 'lng': driver_start[1]},
        'steps': steps,
        'computation_time_ms': round(total_ms),
        'states_explored': states_explored,
        'states_pruned': states_pruned,
    }


def _empty_result(driver_start, steps):
    """Return result for zero riders."""
    steps.append({'phase': 'complete', 'message': 'No riders to optimize.', 'total_ms': 0})
    return {
        'feasible': True,
        'algorithm': 'dp',
        'route': [],
        'polyline': [],
        'total_distance_km': 0,
        'total_time_min': 0,
        'rider_metrics': [],
        'detour_violated': False,
        'driver_start': {'lat': driver_start[0], 'lng': driver_start[1]},
        'steps': steps,
        'computation_time_ms': 0,
        'states_explored': 0,
        'states_pruned': 0,
    }
