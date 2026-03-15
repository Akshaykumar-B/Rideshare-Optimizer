"""Authentication API — register, login, JWT tokens."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import firebase_admin.auth as firebase_auth
from ..extensions import db
from ..models.user import User, DriverProfile
from ..services import firebase_service # Initializing Firebase SDK

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'No data provided'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    role = data.get('role', 'rider').strip().lower()

    if not email or not password or not name:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'Email, password, and name are required'}), 400

    if role not in ('rider', 'driver', 'admin'):
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'Role must be rider, driver, or admin'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'Email already registered'}), 409

    user = User(email=email, name=name, role=role, phone=data.get('phone'))
    user.set_password(password)
    db.session.add(user)

    # Create driver profile if role is driver
    if role == 'driver':
        profile = DriverProfile(
            user=user,
            vehicle_capacity=data.get('vehicle_capacity', 4)
        )
        db.session.add(profile)

    db.session.commit()

    token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
    return jsonify({
        'message': 'Registration successful',
        'token': token,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login and receive JWT token."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'No data provided'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'UNAUTHORIZED', 'message': 'Invalid email or password'}), 401

    token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
    return jsonify({
        'token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/firebase-login', methods=['POST'])
def firebase_login():
    """Login (or register) using a Firebase ID Token from Google Sign-In."""
    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({'error': 'VALIDATION_ERROR', 'message': 'Firebase token is required'}), 400

    id_token = data['token']
    try:
        # 1. Verify the Firebase token
        decoded_token = firebase_auth.verify_id_token(id_token)
        email = decoded_token.get('email')
        
        if not email:
            return jsonify({'error': 'UNAUTHORIZED', 'message': 'Email not provided in token'}), 401
            
        # 2. Find or create the user in our PostgreSQL database
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Auto-register new user from Google profile
            name = decoded_token.get('name', email.split('@')[0])
            
            # Default to rider, unless it's the master admin
            role = 'admin' if email == 'akshaykumarbandam@gmail.com' else 'rider'
            
            user = User(email=email, name=name, role=role)
            user.set_password('firebase_managed_password') # Prevent standard login
            db.session.add(user)
            db.session.commit()
            
        else:
            # If the user exists but is the admin email, ensure they have admin rights
            if email == 'akshaykumarbandam@gmail.com' and user.role != 'admin':
                user.role = 'admin'
                db.session.commit()
                
        # 3. Issue our powerful JWT for the rest of the backend routes to work identically
        flask_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
        
        return jsonify({
            'message': 'Firebase login successful',
            'token': flask_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        print(f"Firebase token verification failed: {e}")
        return jsonify({'error': 'UNAUTHORIZED', 'message': 'Invalid Firebase token'}), 401


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Get current user info."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'UNAUTHORIZED', 'message': 'User not found'}), 404
    result = user.to_dict()
    if user.role == 'driver' and user.driver_profile:
        result['driver_profile'] = user.driver_profile.to_dict()
    return jsonify(result), 200
