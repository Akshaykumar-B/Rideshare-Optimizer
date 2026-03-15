"""Carbon emission savings calculator.

Computes CO₂ saved by ride-sharing vs individual solo rides.
Average car in India: 0.21 kg CO₂ per km.
Average tree absorbs ~21.77 kg CO₂ per year.
"""
import logging
from flask import current_app
from ..extensions import db
from ..models.trip import Trip

logger = logging.getLogger(__name__)


def calculate_carbon_savings(riders_metrics, shared_distance_km):
    """Calculate CO₂ savings for a single shared ride.

    Args:
        riders_metrics: list of rider metric dicts with 'direct_distance_km'
        shared_distance_km: total shared route distance

    Returns:
        dict with savings calculations
    """
    co2_per_km = current_app.config.get('CO2_PER_KM', 0.21)

    solo_total_km = sum(r.get('direct_distance_km', 0) for r in riders_metrics)
    km_saved = max(solo_total_km - shared_distance_km, 0)
    co2_saved_kg = km_saved * co2_per_km

    return {
        'solo_total_km': round(solo_total_km, 2),
        'shared_km': round(shared_distance_km, 2),
        'km_saved': round(km_saved, 2),
        'savings_pct': round((km_saved / solo_total_km * 100) if solo_total_km > 0 else 0, 1),
        'co2_saved_kg': round(co2_saved_kg, 3),
        'trees_equivalent_annual': round(co2_saved_kg / 21.77 * 365, 1),
        'riders_count': len(riders_metrics),
    }


def get_platform_carbon_summary():
    """Get platform-wide CO₂ savings statistics.

    Returns aggregated stats from all completed trips.
    """
    co2_per_km = current_app.config.get('CO2_PER_KM', 0.21)

    trips = Trip.query.filter(Trip.status == 'completed').all()

    total_co2_saved = 0.0
    total_km_saved = 0.0
    total_solo_km = 0.0
    total_shared_km = 0.0
    total_trips = 0
    total_riders = 0

    for trip in trips:
        if trip.co2_saved_kg:
            total_co2_saved += trip.co2_saved_kg
        if trip.solo_total_km and trip.total_distance_km:
            total_solo_km += trip.solo_total_km
            total_shared_km += trip.total_distance_km
            total_km_saved += max(trip.solo_total_km - trip.total_distance_km, 0)
        total_trips += 1
        total_riders += trip.riders.count()

    return {
        'total_trips': total_trips,
        'total_riders': total_riders,
        'total_co2_saved_kg': round(total_co2_saved, 2),
        'total_km_saved': round(total_km_saved, 2),
        'total_solo_km': round(total_solo_km, 2),
        'total_shared_km': round(total_shared_km, 2),
        'avg_savings_pct': round(
            (total_km_saved / total_solo_km * 100) if total_solo_km > 0 else 0, 1
        ),
        'trees_equivalent_annual': round(total_co2_saved / 21.77 * 365, 1),
        'co2_per_km': co2_per_km,
    }
