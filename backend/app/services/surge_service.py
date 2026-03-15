"""Dynamic surge pricing service.

Calculates surge multiplier based on demand/supply ratio per zone.
Uses H3 hexagonal grid for zone bucketing.

Surge tiers:
  demand_ratio < 1.0  → 1.0× (Normal)
  demand_ratio < 2.0  → 1.2× (Slightly busy)
  demand_ratio < 3.0  → 1.5× (Busy)
  demand_ratio >= 3.0 → 2.0× (Very busy, capped)
"""
import logging
from ..extensions import db
from ..models.ride_request import RideRequest
from ..models.user import DriverProfile
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Surge tier thresholds
SURGE_TIERS = [
    (1.0, 1.0, 'normal', '#22c55e'),       # Green
    (2.0, 1.2, 'slightly_busy', '#eab308'), # Yellow
    (3.0, 1.5, 'busy', '#f97316'),          # Orange
    (float('inf'), 2.0, 'very_busy', '#ef4444'),  # Red
]


def calculate_surge_for_location(lat, lng, radius_km=3.0):
    """Calculate surge multiplier for a specific location.

    Args:
        lat, lng: coordinates to check
        radius_km: radius to count demand/supply

    Returns:
        dict with surge_multiplier, tier, color, demand/supply counts
    """
    try:
        # Try H3-based zone lookup
        h3_cell = _get_h3_cell(lat, lng)
        if h3_cell:
            return _calculate_surge_by_h3(h3_cell)
    except Exception:
        pass

    # Fallback: count nearby requests and drivers
    return _calculate_surge_by_proximity(lat, lng, radius_km)


def _get_h3_cell(lat, lng, resolution=7):
    """Get H3 cell for a location."""
    try:
        import h3
        return h3.latlng_to_cell(lat, lng, resolution)
    except ImportError:
        return None


def _calculate_surge_by_h3(h3_cell):
    """Calculate surge using H3 zone bucketing."""
    try:
        import h3
        # Get neighboring cells for broader zone
        neighbors = h3.grid_disk(h3_cell, 1)  # Center + 6 neighbors
        neighbor_list = list(neighbors)
    except ImportError:
        neighbor_list = [h3_cell]

    # Count pending requests in zone
    active_requests = RideRequest.query.filter(
        RideRequest.status.in_(['pending', 'matched']),
        RideRequest.pickup_h3_cell.in_(neighbor_list),
        RideRequest.created_at > datetime.now(timezone.utc) - timedelta(minutes=15)
    ).count()

    # Count available drivers in zone
    available_drivers = DriverProfile.query.filter(
        DriverProfile.is_available == True,
        DriverProfile.h3_cell.in_(neighbor_list)
    ).count()

    return _compute_surge(active_requests, available_drivers)


def _calculate_surge_by_proximity(lat, lng, radius_km):
    """Calculate surge by counting nearby entities (fallback without H3)."""
    # Count recent pending requests (simplified — no spatial index)
    active_requests = RideRequest.query.filter(
        RideRequest.status.in_(['pending', 'matched']),
        RideRequest.created_at > datetime.now(timezone.utc) - timedelta(minutes=15)
    ).count()

    available_drivers = DriverProfile.query.filter(
        DriverProfile.is_available == True
    ).count()

    return _compute_surge(active_requests, available_drivers)


def _compute_surge(active_requests, available_drivers):
    """Compute surge multiplier from demand/supply counts."""
    demand_ratio = active_requests / max(available_drivers, 1)

    for threshold, multiplier, tier_name, color in SURGE_TIERS:
        if demand_ratio < threshold:
            return {
                'surge_multiplier': multiplier,
                'tier': tier_name,
                'color': color,
                'active_requests': active_requests,
                'available_drivers': available_drivers,
                'demand_ratio': round(demand_ratio, 2),
            }

    # Shouldn't reach here, but default to max
    return {
        'surge_multiplier': 2.0,
        'tier': 'very_busy',
        'color': '#ef4444',
        'active_requests': active_requests,
        'available_drivers': available_drivers,
        'demand_ratio': round(demand_ratio, 2),
    }


def get_all_zone_surges():
    """Get surge information for all zones with activity.

    Returns list of zone surge data for frontend heatmap.
    """
    try:
        import h3

        # Get all H3 cells with pending requests
        cells = db.session.query(
            RideRequest.pickup_h3_cell,
            db.func.count(RideRequest.id).label('count')
        ).filter(
            RideRequest.status.in_(['pending', 'matched']),
            RideRequest.pickup_h3_cell.isnot(None),
            RideRequest.created_at > datetime.now(timezone.utc) - timedelta(minutes=30)
        ).group_by(RideRequest.pickup_h3_cell).all()

        zones = []
        for cell, count in cells:
            if not cell:
                continue
            try:
                lat, lng = h3.cell_to_latlng(cell)
                boundary = h3.cell_to_boundary(cell)
                surge = _compute_surge(count, 1)  # Simplified

                zones.append({
                    'h3_cell': cell,
                    'lat': lat,
                    'lng': lng,
                    'boundary': [{'lat': b[0], 'lng': b[1]} for b in boundary],
                    'request_count': count,
                    **surge,
                })
            except Exception:
                continue

        return zones

    except ImportError:
        return []
