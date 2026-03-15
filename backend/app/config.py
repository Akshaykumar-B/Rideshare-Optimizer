"""Application configuration."""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'rideshare-dev-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(os.path.dirname(basedir), "rideshare.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-rideshare-secret-2026')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_TOKEN_LOCATION = ['headers']

    # Graph settings
    GRAPH_FILE = os.environ.get(
        'GRAPH_FILE',
        os.path.join(os.path.dirname(basedir), 'data', 'bangalore_graph.graphml')
    )
    GRAPH_MODE = 'haversine'  # 'osmnx' if graph file exists and loads successfully

    # Fare settings
    BASE_FARE = 30.0         # INR
    RATE_PER_KM = 12.0       # INR per km
    RATE_PER_MIN = 2.0       # INR per minute
    SHARED_DISCOUNT = 0.30   # 30% discount for shared rides

    # Surge settings
    SURGE_CAP = 2.0          # Maximum surge multiplier

    # Carbon settings
    CO2_PER_KM = 0.21        # kg CO2 per km (average car in India)

    # Matching settings
    MAX_PICKUP_RADIUS_KM = 5.0
    MAX_DETOUR_RATIO = 1.5
    MAX_DP_RIDERS = 8

    # Speed defaults (km/h) when no graph available
    DEFAULT_SPEED_KMH = 25.0  # Average Bangalore traffic speed


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
