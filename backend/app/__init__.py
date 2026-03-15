"""Flask application factory for RideShare Optimizer."""
import os
from flask import Flask
from flask_cors import CORS

from .extensions import db, jwt, migrate
from .config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from .api.auth import auth_bp
    from .api.riders import riders_bp
    from .api.drivers import drivers_bp
    from .api.trips import trips_bp
    from .api.analytics import analytics_bp
    from .api.surge import surge_bp
    from .api.demo import demo_bp

    from .api.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(riders_bp, url_prefix='/api/rides')
    app.register_blueprint(drivers_bp, url_prefix='/api/drivers')
    app.register_blueprint(trips_bp, url_prefix='/api/trips')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(surge_bp, url_prefix='/api/surge')
    app.register_blueprint(demo_bp, url_prefix='/api/demo')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Health check
    @app.route('/api/health')
    def health():
        return {'status': 'healthy', 'graph_mode': app.config.get('GRAPH_MODE', 'haversine')}

    # Create tables on first request
    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    return app
