"""Trip and TripRider models."""
from datetime import datetime, timezone
from ..extensions import db


class Trip(db.Model):
    """An active or completed trip with an optimized route."""
    __tablename__ = 'trips'

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver_profiles.id'), nullable=False)

    # Trip status
    status = db.Column(
        db.String(20), nullable=False, default='active'
    )  # active, completed, cancelled

    # Route data (JSON: ordered list of stop objects)
    route_sequence = db.Column(db.JSON, nullable=True)

    # Metrics
    total_distance_km = db.Column(db.Float, nullable=True)
    total_time_min = db.Column(db.Float, nullable=True)
    algorithm_used = db.Column(db.String(20), nullable=True)  # dp, greedy_nn, greedy_ci

    # Carbon savings
    co2_saved_kg = db.Column(db.Float, default=0.0)
    solo_total_km = db.Column(db.Float, nullable=True)

    # Surge info
    surge_multiplier = db.Column(db.Float, default=1.0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    riders = db.relationship('TripRider', backref='trip', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'driver_id': self.driver_id,
            'status': self.status,
            'route_sequence': self.route_sequence,
            'total_distance_km': self.total_distance_km,
            'total_time_min': self.total_time_min,
            'algorithm_used': self.algorithm_used,
            'co2_saved_kg': self.co2_saved_kg,
            'solo_total_km': self.solo_total_km,
            'surge_multiplier': self.surge_multiplier,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'riders': [r.to_dict() for r in self.riders],
        }


class TripRider(db.Model):
    """Association between a trip and a rider, with per-rider metrics."""
    __tablename__ = 'trip_riders'

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    ride_request_id = db.Column(db.Integer, db.ForeignKey('ride_requests.id'), nullable=False, index=True)

    # Fare
    fare_amount = db.Column(db.Float, nullable=True)
    shapley_fare = db.Column(db.Float, nullable=True)  # Internal fairness value
    solo_fare = db.Column(db.Float, nullable=True)      # What they'd pay alone

    # Distance metrics
    direct_distance_km = db.Column(db.Float, nullable=True)
    actual_distance_km = db.Column(db.Float, nullable=True)
    detour_ratio = db.Column(db.Float, nullable=True)

    # Stop ordering
    pickup_order = db.Column(db.Integer, nullable=True)
    dropoff_order = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'trip_id': self.trip_id,
            'ride_request_id': self.ride_request_id,
            'fare_amount': self.fare_amount,
            'shapley_fare': self.shapley_fare,
            'solo_fare': self.solo_fare,
            'direct_distance_km': self.direct_distance_km,
            'actual_distance_km': self.actual_distance_km,
            'detour_ratio': self.detour_ratio,
            'pickup_order': self.pickup_order,
            'dropoff_order': self.dropoff_order,
        }
