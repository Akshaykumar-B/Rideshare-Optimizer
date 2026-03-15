from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from ..extensions import db
from ..models.user import User, DriverProfile

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Returns a list of all registered users (Admin only)."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'FORBIDDEN', 'message': 'Admin privileges required'}), 403
        
    users = User.query.all()
    user_list = []
    
    for u in users:
        user_data = u.to_dict()
        user_data['driver_profile'] = bool(u.driver_profile)
        user_list.append(user_data)
        
    return jsonify({'users': user_list}), 200


@admin_bp.route('/promote/<int:user_id>', methods=['PUT'])
@jwt_required()
def promote_to_driver(user_id):
    """Promotes a rider to a driver (Admin only)."""
    # 1. Verify caller is an admin
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'FORBIDDEN', 'message': 'Admin privileges required'}), 403

    # 2. Find the user
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'NOT_FOUND', 'message': 'User not found'}), 404

    # 3. Check if already a driver
    if user.role == 'driver':
        return jsonify({'message': 'User is already a driver'}), 200
        
    # 4. Promote and create driver profile
    user.role = 'driver'
    
    # Create driver profile if they don't have one
    if not user.driver_profile:
        profile = DriverProfile(
            user=user,
            vehicle_capacity=4 # Default
        )
        db.session.add(profile)
        
    db.session.commit()
    
    return jsonify({
        'message': f'User {user.email} successfully promoted to driver',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/demote/<int:user_id>', methods=['PUT'])
@jwt_required()
def demote_to_rider(user_id):
    """Demotes a driver back to a rider (Admin only)."""
    # 1. Verify caller is an admin
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'FORBIDDEN', 'message': 'Admin privileges required'}), 403

    # 2. Find the user
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'NOT_FOUND', 'message': 'User not found'}), 404

    # 3. Check if already a rider
    if user.role == 'rider':
        return jsonify({'message': 'User is already a rider'}), 200
        
    # 4. Demote
    user.role = 'rider'
    
    # Set driver profile availability to False if it exists
    if user.driver_profile:
        user.driver_profile.is_available = False
        
    db.session.commit()
    
    return jsonify({
        'message': f'User {user.email} successfully demoted to rider',
        'user': user.to_dict()
    }), 200
