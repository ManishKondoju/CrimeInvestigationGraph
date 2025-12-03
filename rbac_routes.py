"""
Authentication and User Management API Routes
Flask blueprints for RBAC system endpoints
"""

from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import re

from models import User, Role, Permission, ActivityLog, Case
from Auth_middleware import (
    login_required, require_permission, require_role,
    SessionManager, ResourceAccessControl, log_activity
)
from RBAC_config import Role as RoleEnum, Permission as PermissionEnum
from database import db_session

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
user_bp = Blueprint('users', __name__, url_prefix='/api/users')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============== Authentication Routes ==============

@auth_bp.route('/register', methods=['POST'])
@log_activity("User registration", "user")
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'fields': missing_fields
        }), 400
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password strength
    password = data['password']
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400
    if not any(c.isupper() for c in password):
        return jsonify({'error': 'Password must contain at least one uppercase letter'}), 400
    if not any(c.islower() for c in password):
        return jsonify({'error': 'Password must contain at least one lowercase letter'}), 400
    if not any(c.isdigit() for c in password):
        return jsonify({'error': 'Password must contain at least one digit'}), 400
    
    try:
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            badge_number=data.get('badge_number'),
            department=data.get('department'),
            phone=data.get('phone')
        )
        
        # Assign default role (Guest or Viewer)
        default_role = db_session.query(Role).filter_by(name='viewer').first()
        if default_role:
            user.roles.append(default_role)
        
        db_session.add(user)
        db_session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except IntegrityError as e:
        db_session.rollback()
        if 'username' in str(e):
            return jsonify({'error': 'Username already exists'}), 409
        elif 'email' in str(e):
            return jsonify({'error': 'Email already registered'}), 409
        elif 'badge_number' in str(e):
            return jsonify({'error': 'Badge number already registered'}), 409
        else:
            return jsonify({'error': 'Registration failed'}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    # Find user by username or email
    user = db_session.query(User).filter(
        (User.username == data['username']) | (User.email == data['username'])
    ).first()
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check if account is locked
    if user.is_locked():
        return jsonify({
            'error': 'Account locked',
            'message': 'Too many failed login attempts. Please try again later.'
        }), 403
    
    # Verify password
    if not user.check_password(data['password']):
        db_session.commit()  # Save failed attempt count
        remaining_attempts = 5 - user.failed_login_attempts
        return jsonify({
            'error': 'Invalid credentials',
            'remaining_attempts': remaining_attempts
        }), 401
    
    # Check if account is active
    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403
    
    # Create session
    remember_me = data.get('remember_me', False)
    session = SessionManager.create_session(user, remember_me)
    
    db_session.commit()
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(include_sensitive=True),
        **session
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout"""
    user = g.current_user
    SessionManager.invalidate_session(user)
    db_session.commit()
    
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh authentication token"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400
    
    new_session = SessionManager.refresh_session(refresh_token)
    if not new_session:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401
    
    return jsonify(new_session), 200

@auth_bp.route('/verify', methods=['GET'])
@login_required
def verify_token():
    """Verify current authentication token"""
    user = g.current_user
    return jsonify({
        'valid': True,
        'user': user.to_dict(include_sensitive=True)
    }), 200

# ============== User Management Routes ==============

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    user = g.current_user
    return jsonify(user.to_dict(include_sensitive=True)), 200

@user_bp.route('/profile', methods=['PUT'])
@login_required
@log_activity("Update profile", "user")
def update_profile():
    """Update current user profile"""
    user = g.current_user
    data = request.get_json()
    
    # Fields that users can update themselves
    allowed_fields = ['first_name', 'last_name', 'phone', 'email']
    
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    # Update password if provided
    if 'current_password' in data and 'new_password' in data:
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        password = data['new_password']
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        user.set_password(password)
    
    user.updated_at = datetime.utcnow()
    
    try:
        db_session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    except IntegrityError:
        db_session.rollback()
        return jsonify({'error': 'Email already in use'}), 409

@user_bp.route('/permissions', methods=['GET'])
@login_required
def get_my_permissions():
    """Get current user's permissions"""
    user = g.current_user
    return jsonify({
        'roles': [role.to_dict() for role in user.roles],
        'permissions': list(user.get_permissions())
    }), 200

@user_bp.route('/cases', methods=['GET'])
@login_required
def get_my_cases():
    """Get cases assigned to current user"""
    user = g.current_user
    cases = []
    
    for case in user.assigned_cases:
        # Filter sensitive data based on permissions
        case_data = {
            'id': case.id,
            'case_number': case.case_number,
            'title': case.title,
            'status': case.status,
            'sensitivity': case.sensitivity,
            'created_at': case.created_at.isoformat() if case.created_at else None
        }
        
        # Add filtered data
        filtered_case = ResourceAccessControl.filter_sensitive_data(
            user, case_data, 'case'
        )
        cases.append(filtered_case)
    
    return jsonify({'cases': cases}), 200

# ============== Admin Routes ==============

@admin_bp.route('/users', methods=['GET'])
@require_role([RoleEnum.ADMIN, RoleEnum.CHIEF_OFFICER])
def list_users():
    """List all users (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Query users with pagination
    users_query = db_session.query(User)
    
    # Apply filters if provided
    if request.args.get('role'):
        role_name = request.args.get('role')
        users_query = users_query.join(User.roles).filter(Role.name == role_name)
    
    if request.args.get('department'):
        users_query = users_query.filter(User.department == request.args.get('department'))
    
    if request.args.get('active') is not None:
        is_active = request.args.get('active', type=bool)
        users_query = users_query.filter(User.is_active == is_active)
    
    # Paginate
    total = users_query.count()
    users = users_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'users': [user.to_dict() for user in users],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }), 200

@admin_bp.route('/users/<user_id>', methods=['GET'])
@require_permission(PermissionEnum.VIEW_USER)
def get_user(user_id):
    """Get specific user details"""
    user = db_session.query(User).filter_by(id=user_id).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict(include_sensitive=True)), 200

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@require_permission(PermissionEnum.UPDATE_USER)
@log_activity("Update user", "user")
def update_user(user_id):
    """Update user details (admin only)"""
    user = db_session.query(User).filter_by(id=user_id).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Admin can update more fields
    admin_fields = ['username', 'email', 'first_name', 'last_name', 
                   'badge_number', 'department', 'phone', 'is_active', 'is_verified']
    
    for field in admin_fields:
        if field in data:
            setattr(user, field, data[field])
    
    user.updated_at = datetime.utcnow()
    
    try:
        db_session.commit()
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
    except IntegrityError:
        db_session.rollback()
        return jsonify({'error': 'Update failed - duplicate value'}), 409

@admin_bp.route('/users/<user_id>/roles', methods=['PUT'])
@require_permission(PermissionEnum.ASSIGN_ROLE)
@log_activity("Assign roles", "user")
def assign_roles(user_id):
    """Assign roles to a user"""
    user = db_session.query(User).filter_by(id=user_id).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    role_names = data.get('roles', [])
    
    # Clear existing roles
    user.roles.clear()
    
    # Assign new roles
    for role_name in role_names:
        role = db_session.query(Role).filter_by(name=role_name).first()
        if role:
            user.roles.append(role)
    
    db_session.commit()
    
    return jsonify({
        'message': 'Roles assigned successfully',
        'user': user.to_dict(include_sensitive=True)
    }), 200

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@require_permission(PermissionEnum.DELETE_USER)
@log_activity("Delete user", "user")
def delete_user(user_id):
    """Delete a user (soft delete)"""
    user = db_session.query(User).filter_by(id=user_id).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Don't allow deleting admin
    if user.has_role('admin'):
        return jsonify({'error': 'Cannot delete admin user'}), 403
    
    # Soft delete (deactivate)
    user.is_active = False
    SessionManager.invalidate_session(user)
    
    db_session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200

@admin_bp.route('/roles', methods=['GET'])
@require_permission(PermissionEnum.VIEW_USER)
def list_roles():
    """List all available roles"""
    roles = db_session.query(Role).all()
    return jsonify({
        'roles': [role.to_dict() for role in roles]
    }), 200

@admin_bp.route('/permissions', methods=['GET'])
@require_permission(PermissionEnum.VIEW_USER)
def list_permissions():
    """List all available permissions"""
    permissions = db_session.query(Permission).all()
    return jsonify({
        'permissions': [perm.to_dict() for perm in permissions]
    }), 200

@admin_bp.route('/activity-logs', methods=['GET'])
@require_permission(PermissionEnum.VIEW_LOGS)
def get_activity_logs():
    """Get system activity logs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Query logs
    logs_query = db_session.query(ActivityLog).order_by(ActivityLog.timestamp.desc())
    
    # Apply filters
    if request.args.get('user_id'):
        logs_query = logs_query.filter(ActivityLog.user_id == request.args.get('user_id'))
    
    if request.args.get('action'):
        logs_query = logs_query.filter(ActivityLog.action.contains(request.args.get('action')))
    
    if request.args.get('resource_type'):
        logs_query = logs_query.filter(ActivityLog.resource_type == request.args.get('resource_type'))
    
    # Paginate
    total = logs_query.count()
    logs = logs_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }), 200

# Export blueprints
__all__ = ['auth_bp', 'user_bp', 'admin_bp']