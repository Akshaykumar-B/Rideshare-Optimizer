"""Graph service — road network, shortest paths, distance matrices.

Supports two modes:
1. 'osmnx' — real Bangalore road graph with A* search (if GraphML file exists)
2. 'haversine' — haversine distance × 1.4 road factor fallback (no dependencies)
"""
import os
import time
import logging
from math import radians, sin, cos, sqrt, atan2
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)

# Module-level singleton for the road graph
_graph = None
_graph_mode = 'haversine'

# Road factor: haversine × this = approximate road distance
ROAD_FACTOR = 1.4

# Default speed in m/s (~25 km/h, typical Bangalore traffic)
DEFAULT_SPEED_MS = 25.0 * 1000 / 3600


def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate haversine distance in meters between two points."""
    R = 6371000  # Earth's radius in meters
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def haversine_travel_time(lat1, lng1, lat2, lng2):
    """Estimate travel time in seconds using haversine distance × road factor."""
    dist = haversine_distance(lat1, lng1, lat2, lng2) * ROAD_FACTOR
    return dist / DEFAULT_SPEED_MS


def haversine_road_distance(lat1, lng1, lat2, lng2):
    """Estimate road distance in meters using haversine × road factor."""
    return haversine_distance(lat1, lng1, lat2, lng2) * ROAD_FACTOR


def init_graph(graph_file=None):
    """Initialize the road graph. Called once on app startup."""
    global _graph, _graph_mode

    if graph_file and os.path.exists(graph_file):
        try:
            import osmnx as ox
            import networkx as nx

            logger.info(f"Loading road graph from {graph_file}...")
            start = time.time()
            _graph = ox.load_graphml(graph_file)

            # Add edge speeds and travel times
            _graph = ox.routing.add_edge_speeds(_graph)
            _graph = ox.routing.add_edge_travel_times(_graph)

            _graph_mode = 'osmnx'
            elapsed = time.time() - start
            logger.info(
                f"Graph loaded: {_graph.number_of_nodes()} nodes, "
                f"{_graph.number_of_edges()} edges in {elapsed:.1f}s"
            )
        except Exception as e:
            logger.warning(f"Failed to load graph: {e}. Falling back to haversine.")
            _graph = None
            _graph_mode = 'haversine'
    else:
        logger.info("No graph file found. Using haversine fallback.")
        _graph_mode = 'haversine'


def get_graph_mode():
    """Return current graph mode."""
    return _graph_mode


def nearest_node(lat, lng):
    """Find the nearest graph node to a lat/lng coordinate.

    Returns node ID if graph is available, or (lat, lng) tuple for haversine mode.
    """
    if _graph_mode == 'osmnx' and _graph is not None:
        import osmnx as ox
        return ox.nearest_nodes(_graph, lng, lat)
    else:
        return (lat, lng)


def _a_star_heuristic(u, v):
    """Admissible heuristic for A* on road networks.

    Uses haversine distance / max_road_speed as lower bound on travel time.
    """
    lat1 = _graph.nodes[u]['y']
    lng1 = _graph.nodes[u]['x']
    lat2 = _graph.nodes[v]['y']
    lng2 = _graph.nodes[v]['x']
    dist = haversine_distance(lat1, lng1, lat2, lng2)
    # Max road speed ~80 km/h = 22.2 m/s → lower bound on travel time
    return dist / 22.2


@lru_cache(maxsize=50000)
def shortest_path_time(node1, node2):
    """Compute shortest path travel time (seconds) between two nodes.

    Cached with LRU for O(1) repeated lookups.
    """
    if _graph_mode == 'osmnx' and _graph is not None:
        import networkx as nx
        try:
            return nx.astar_path_length(
                _graph, node1, node2,
                heuristic=_a_star_heuristic,
                weight='travel_time'
            )
        except nx.NetworkXNoPath:
            # Fallback to haversine if no path exists
            lat1, lng1 = _graph.nodes[node1]['y'], _graph.nodes[node1]['x']
            lat2, lng2 = _graph.nodes[node2]['y'], _graph.nodes[node2]['x']
            return haversine_travel_time(lat1, lng1, lat2, lng2)
    else:
        # Haversine mode: node1 and node2 are (lat, lng) tuples
        return haversine_travel_time(node1[0], node1[1], node2[0], node2[1])


@lru_cache(maxsize=50000)
def shortest_path_distance(node1, node2):
    """Compute shortest path distance (meters) between two nodes."""
    if _graph_mode == 'osmnx' and _graph is not None:
        import networkx as nx
        try:
            return nx.astar_path_length(
                _graph, node1, node2,
                heuristic=lambda u, v: haversine_distance(
                    _graph.nodes[u]['y'], _graph.nodes[u]['x'],
                    _graph.nodes[v]['y'], _graph.nodes[v]['x']
                ),
                weight='length'
            )
        except nx.NetworkXNoPath:
            lat1, lng1 = _graph.nodes[node1]['y'], _graph.nodes[node1]['x']
            lat2, lng2 = _graph.nodes[node2]['y'], _graph.nodes[node2]['x']
            return haversine_road_distance(lat1, lng1, lat2, lng2)
    else:
        return haversine_road_distance(node1[0], node1[1], node2[0], node2[1])


def shortest_path_route(node1, node2):
    """Get the full shortest path as a list of (lat, lng) coordinates for map display."""
    if _graph_mode == 'osmnx' and _graph is not None:
        import networkx as nx
        try:
            path = nx.astar_path(
                _graph, node1, node2,
                heuristic=_a_star_heuristic,
                weight='travel_time'
            )
            return [(_graph.nodes[n]['y'], _graph.nodes[n]['x']) for n in path]
        except nx.NetworkXNoPath:
            pass

    # Fallback: straight line with intermediate points
    if isinstance(node1, tuple):
        lat1, lng1 = node1
        lat2, lng2 = node2
    else:
        lat1, lng1 = _graph.nodes[node1]['y'], _graph.nodes[node1]['x']
        lat2, lng2 = _graph.nodes[node2]['y'], _graph.nodes[node2]['x']

    # Generate 10 intermediate points for smooth polyline
    points = []
    for i in range(11):
        t = i / 10
        lat = lat1 + t * (lat2 - lat1)
        lng = lng1 + t * (lng2 - lng1)
        points.append((lat, lng))
    return points


def precompute_distance_matrix(locations):
    """Precompute all-pairs travel time and distance matrices.

    Args:
        locations: list of (lat, lng) tuples.
                   Index 0 = driver start, 1..n = pickups, n+1..2n = dropoffs.

    Returns:
        time_matrix: numpy array of travel times (seconds)
        dist_matrix: numpy array of distances (meters)
        nodes: list of graph node IDs (or (lat,lng) tuples in haversine mode)
        computation_time_ms: time taken to compute the matrix
    """
    start = time.time()
    n = len(locations)
    nodes = [nearest_node(lat, lng) for lat, lng in locations]

    time_matrix = np.zeros((n, n))
    dist_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i != j:
                time_matrix[i][j] = shortest_path_time(nodes[i], nodes[j])
                dist_matrix[i][j] = shortest_path_distance(nodes[i], nodes[j])

    computation_time_ms = (time.time() - start) * 1000

    return time_matrix, dist_matrix, nodes, computation_time_ms


def get_route_polyline(locations):
    """Get a full route polyline through a sequence of locations.

    Args:
        locations: list of (lat, lng) tuples in visit order.

    Returns:
        list of (lat, lng) points forming the complete route polyline.
    """
    if len(locations) < 2:
        return locations

    nodes = [nearest_node(lat, lng) for lat, lng in locations]
    full_route = []

    for i in range(len(nodes) - 1):
        segment = shortest_path_route(nodes[i], nodes[i + 1])
        if i > 0 and segment:
            segment = segment[1:]  # Skip duplicate first point
        full_route.extend(segment)

    return full_route
