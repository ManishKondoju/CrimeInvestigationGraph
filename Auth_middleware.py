"""
Authentication and Authorization Middleware
Decorators and middleware for protecting routes with RBAC
"""

from functools import wraps
from typing import List, Optional, Union
from flask import request, jsonify, g, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
import jwt
from datetime import datetime
from models import User, ActivityLog, Role
from RBAC_config import Permission, Role as RoleEnum

class AuthMiddleware:
    """Authentication middleware for Flask applications"""
    
    @staticmethod
    def authenticate_request():
        """Authenticate the incoming request"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        try:
            # Extract token from "Bearer <token>" format
            parts = auth_header.split()
            if parts[0].lower() != 'bearer' or len(parts) != 2:
                return None
            
            token = parts[1]
            secret_key = current_app.config.get('SECRET_KEY')
            payload = User.verify_auth_token(token, secret_key)
            
            if payload:
                # Get user from database
                from database import db_session
                user = db_session.query(User).filter_by(id=payload['user_id']).first()
                if user and user.is_active:
                    g.current_user = user
                    return user
            return None
        except Exception as e:
            current_app.logger.error(f"Authentication error: {e}")
            return None

def login_required(f):
    """Decorator to require authentication for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = AuthMiddleware.authenticate_request()
        if not user:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please provide a valid authentication token'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def require_permission(permission: Union[str, Permission]):
    """Decorator to require specific permission for a route"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            # Convert Permission enum to string if needed
            permission_name = permission.value if isinstance(permission, Permission) else permission
            
            if not user.has_permission(permission_name):
                # Log unauthorized access attempt
                ActivityLog.log(
                    user_id=user.id,
                    action=f"Unauthorized access attempt: {permission_name}",
                    resource_type="permission",
                    success=False
                )
                
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'You do not have permission to perform this action',
                    'required_permission': permission_name
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(role: Union[str, RoleEnum, List[Union[str, RoleEnum]]]):
    """Decorator to require specific role(s) for a route"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            # Convert to list if single role
            roles = role if isinstance(role, list) else [role]
            
            # Convert RoleEnum to string if needed
            role_names = [r.value if isinstance(r, RoleEnum) else r for r in roles]
            
            # Check if user has any of the required roles
            if not any(user.has_role(role_name) for role_name in role_names):
                # Log unauthorized access attempt
                ActivityLog.log(
                    user_id=user.id,
                    action=f"Unauthorized role access attempt: {role_names}",
                    resource_type="role",
                    success=False
                )
                
                return jsonify({
                    'error': 'Insufficient role privileges',
                    'message': 'You do not have the required role to access this resource',
                    'required_roles': role_names
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_case_access(case_id_param: str = 'case_id'):
    """Decorator to check if user has access to a specific case"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user = g.current_user
            case_id = kwargs.get(case_id_param) or request.args.get(case_id_param)
            
            if not case_id:
                return jsonify({
                    'error': 'Case ID required',
                    'message': 'Please provide a valid case ID'
                }), 400
            
            if not user.can_access_case(case_id):
                ActivityLog.log(
                    user_id=user.id,
                    action=f"Unauthorized case access attempt",
                    resource_type="case",
                    resource_id=case_id,
                    success=False
                )
                
                return jsonify({
                    'error': 'Access denied',
                    'message': 'You do not have access to this case'
                }), 403
            
            # Store case_id in g for use in the route
            g.case_id = case_id
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_activity(action: str, resource_type: str = None):
    """Decorator to log user activity"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function
            result = f(*args, **kwargs)
            
            # Log the activity if user is authenticated
            if hasattr(g, 'current_user'):
                resource_id = kwargs.get('id') or kwargs.get(f'{resource_type}_id')
                ActivityLog.log(
                    user_id=g.current_user.id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details={
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'args': dict(request.args),
                        'ip': request.remote_addr
                    },
                    success=True
                )
            
            return result
        return decorated_function
    return decorator

def rate_limit(max_requests: int = 100, window: int = 3600):
    """Decorator to implement rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if hasattr(g, 'current_user'):
                # Implement rate limiting logic here
                # This is a simplified version - use Redis for production
                from datetime import timedelta
                user = g.current_user
                
                # Check recent requests (simplified)
                recent_requests = getattr(user, '_request_count', 0)
                if recent_requests >= max_requests:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {max_requests} requests per {window} seconds'
                    }), 429
                
                # Increment counter (in production, use Redis)
                user._request_count = recent_requests + 1
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class ResourceAccessControl:
    """Fine-grained resource access control"""
    
    @staticmethod
    def can_view_evidence(user: User, evidence_type: str, case_sensitivity: str) -> bool:
        """Check if user can view specific evidence"""
        # Forensic evidence requires special permissions
        if evidence_type in ["DNA", "FORENSIC", "BALLISTICS"]:
            if not user.has_permission("view_evidence"):
                return False
            
            # High sensitivity requires higher role
            if case_sensitivity == "HIGH":
                return user.has_role("detective") or \
                       user.has_role("chief_officer") or \
                       user.has_role("admin")
        
        return user.has_permission("view_evidence")
    
    @staticmethod
    def can_modify_suspect(user: User, suspect_status: str) -> bool:
        """Check if user can modify suspect information"""
        # Arrested suspects require higher clearance
        if suspect_status in ["ARRESTED", "CONVICTED"]:
            return user.has_role("detective") or \
                   user.has_role("chief_officer") or \
                   user.has_role("admin")
        
        return user.has_permission("update_suspect")
    
    @staticmethod
    def filter_sensitive_data(user: User, data: dict, resource_type: str) -> dict:
        """Filter sensitive data based on user permissions"""
        filtered_data = data.copy()
        
        # Define sensitive fields per resource type
        sensitive_fields = {
            "witness": ["address", "phone", "ssn"],
            "suspect": ["criminal_history", "associates"],
            "evidence": ["chain_of_custody", "internal_notes"],
            "case": ["confidential_notes", "internal_assessment"]
        }
        
        # Remove sensitive fields if user doesn't have full access
        if not user.has_role("admin") and not user.has_role("chief_officer"):
            fields_to_remove = sensitive_fields.get(resource_type, [])
            for field in fields_to_remove:
                filtered_data.pop(field, None)
        
        return filtered_data

class SessionManager:
    """Manage user sessions and tokens"""
    
    @staticmethod
    def create_session(user: User, remember_me: bool = False) -> dict:
        """Create a new session for the user"""
        from datetime import timedelta
        
        # Token expiration times
        access_expires = timedelta(hours=1)
        refresh_expires = timedelta(days=30 if remember_me else 7)
        
        # Generate tokens
        secret_key = current_app.config.get('SECRET_KEY')
        access_token = user.generate_auth_token(
            secret_key, 
            expires_in=int(access_expires.total_seconds())
        )
        
        refresh_payload = {
            'user_id': user.id,
            'type': 'refresh',
            'exp': datetime.utcnow() + refresh_expires
        }
        refresh_token = jwt.encode(refresh_payload, secret_key, algorithm='HS256')
        
        # Store refresh token
        user.refresh_token = refresh_token
        
        # Log successful login
        ActivityLog.log(
            user_id=user.id,
            action="User login",
            details={'remember_me': remember_me}
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(access_expires.total_seconds())
        }
    
    @staticmethod
    def refresh_session(refresh_token: str) -> Optional[dict]:
        """Refresh an existing session"""
        try:
            secret_key = current_app.config.get('SECRET_KEY')
            payload = jwt.decode(refresh_token, secret_key, algorithms=['HS256'])
            
            if payload.get('type') != 'refresh':
                return None
            
            # Get user
            from database import db_session
            user = db_session.query(User).filter_by(id=payload['user_id']).first()
            
            if not user or user.refresh_token != refresh_token or not user.is_active:
                return None
            
            # Generate new access token
            access_token = user.generate_auth_token(secret_key, expires_in=3600)
            
            return {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': 3600
            }
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def invalidate_session(user: User):
        """Invalidate all sessions for a user"""
        user.refresh_token = None
        user.active_sessions = []
        
        ActivityLog.log(
            user_id=user.id,
            action="User logout",
            details={'forced': False}
        )

# Export decorators and classes
__all__ = [
    'AuthMiddleware',
    'login_required',
    'require_permission',
    'require_role',
    'require_case_access',
    'log_activity',
    'rate_limit',
    'ResourceAccessControl',
    'SessionManager'
]