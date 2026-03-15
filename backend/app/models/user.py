"""User and DriverProfile models."""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class User(db.Model):
    """User model supporting rider, driver, and admin roles."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(10), nullable=False, default='rider')  # rider, driver, admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    driver_profile = db.relationship('DriverProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    ride_requests = db.relationship('RideRequest', backref='rider', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DriverProfile(db.Model):
    """Extended profile for driver users."""
    __tablename__ = 'driver_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    vehicle_capacity = db.Column(db.Integer, default=4)
    is_available = db.Column(db.Boolean, default=False, index=True)
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    h3_cell = db.Column(db.String(20), nullable=True, index=True)
    current_load = db.Column(db.Integer, default=0)  # Current passengers onboard

    # Relationships
    trips = db.relationship('Trip', backref='driver_profile', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle_capacity': self.vehicle_capacity,
            'is_available': self.is_available,
            'current_lat': self.current_lat,
            'current_lng': self.current_lng,
            'h3_cell': self.h3_cell,
            'current_load': self.current_load,
        }
