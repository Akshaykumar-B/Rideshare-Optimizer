"""RideRequest model."""
from datetime import datetime, timezone
from ..extensions import db


class RideRequest(db.Model):
    """A rider's request for a ride with pickup/dropoff and time window."""
    __tablename__ = 'ride_requests'

    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Locations
    pickup_lat = db.Column(db.Float, nullable=False)
    pickup_lng = db.Column(db.Float, nullable=False)
    dropoff_lat = db.Column(db.Float, nullable=False)
    dropoff_lng = db.Column(db.Float, nullable=False)
    pickup_address = db.Column(db.String(255), nullable=True)
    dropoff_address = db.Column(db.String(255), nullable=True)

    # Time window
    earliest_pickup = db.Column(db.DateTime, nullable=True)
    latest_pickup = db.Column(db.DateTime, nullable=True)

    # Status tracking
    status = db.Column(
        db.String(20), nullable=False, default='pending', index=True
    )  # pending, matched, in_progress, completed, cancelled

    # H3 cell for spatial indexing
    pickup_h3_cell = db.Column(db.String(20), nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to trip assignment
    trip_assignment = db.relationship('TripRider', backref='ride_request', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'rider_id': self.rider_id,
            'pickup_lat': self.pickup_lat,
            'pickup_lng': self.pickup_lng,
            'dropoff_lat': self.dropoff_lat,
            'dropoff_lng': self.dropoff_lng,
            'pickup_address': self.pickup_address,
            'dropoff_address': self.dropoff_address,
            'earliest_pickup': self.earliest_pickup.isoformat() if self.earliest_pickup else None,
            'latest_pickup': self.latest_pickup.isoformat() if self.latest_pickup else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
