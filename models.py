"""
User Model with RBAC Integration
Database model for users with role-based access control
"""

from datetime import datetime
from typing import List, Optional, Dict
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table, Integer, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
import secrets

Base = declarative_base()

# Association table for many-to-many relationship between users and roles
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('role_id', String, ForeignKey('roles.id')),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', String, ForeignKey('users.id'))
)

# Association table for user-case assignments
user_cases = Table('user_cases', Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('case_id', String, ForeignKey('cases.id')),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('role_in_case', String)  # Lead, Assistant, Observer
)

class User(Base):
    """User model with RBAC support"""
    __tablename__ = 'users'
    
    # Basic user information
    id = Column(String, primary_key=True, default=lambda: secrets.token_hex(16))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(50))
    last_name = Column(String(50))
    badge_number = Column(String(20), unique=True)
    department = Column(String(100))
    phone = Column(String(20))
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(32))
    
    # Session management
    active_sessions = Column(JSON, default=list)  # Store active session tokens
    refresh_token = Column(String(255))
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    assigned_cases = relationship("Case", secondary=user_cases, back_populates="assigned_users")
    activity_logs = relationship("ActivityLog", back_populates="user")
    
    def __init__(self, username: str, email: str, password: str, **kwargs):
        """Initialize user with hashed password"""
        self.username = username
        self.email = email
        self.set_password(password)
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, password: str):
        """Set hashed password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password"""
        if self.is_locked():
            return False
        
        result = check_password_hash(self.password_hash, password)
        if not result:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                self.lock_account()
        else:
            self.failed_login_attempts = 0
            self.last_login = datetime.utcnow()
        return result
    
    def lock_account(self, duration_minutes: int = 30):
        """Lock account after failed attempts"""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def get_permissions(self) -> set:
        """Get all permissions for this user"""
        permissions = set()
        for role in self.roles:
            permissions.update(role.get_permissions())
        return permissions
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission"""
        return permission_name in self.get_permissions()
    
    def can_access_case(self, case_id: str) -> bool:
        """Check if user can access a specific case"""
        # Check if user is assigned to the case
        if any(case.id == case_id for case in self.assigned_cases):
            return True
        # Check if user has general case viewing permission
        return self.has_permission("view_case")
    
    def generate_auth_token(self, secret_key: str, expires_in: int = 3600) -> str:
        """Generate JWT authentication token"""
        from datetime import timedelta
        payload = {
            'user_id': self.id,
            'username': self.username,
            'roles': [role.name for role in self.roles],
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
    @staticmethod
    def verify_auth_token(token: str, secret_key: str) -> Optional[Dict]:
        """Verify JWT authentication token"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def to_dict(self, include_sensitive: bool = False) -> Dict:
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'badge_number': self.badge_number,
            'department': self.department,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'roles': [role.name for role in self.roles],
            'mfa_enabled': self.mfa_enabled
        }
        
        if include_sensitive:
            data['permissions'] = list(self.get_permissions())
            data['assigned_cases'] = [case.id for case in self.assigned_cases]
        
        return data

class Role(Base):
    """Role model for RBAC"""
    __tablename__ = 'roles'
    
    id = Column(String, primary_key=True, default=lambda: secrets.token_hex(16))
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    priority = Column(Integer, default=0)  # Higher number = higher priority
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    
    def get_permissions(self) -> List[str]:
        """Get all permission names for this role"""
        return [perm.name for perm in self.permissions]
    
    def add_permission(self, permission):
        """Add a permission to this role"""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission):
        """Remove a permission from this role"""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def to_dict(self) -> Dict:
        """Convert role to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'priority': self.priority,
            'permissions': self.get_permissions(),
            'user_count': len(self.users)
        }

# Association table for role-permission relationship
role_permissions = Table('role_permissions', Base.metadata,
    Column('role_id', String, ForeignKey('roles.id')),
    Column('permission_id', String, ForeignKey('permissions.id'))
)

class Permission(Base):
    """Permission model for fine-grained access control"""
    __tablename__ = 'permissions'
    
    id = Column(String, primary_key=True, default=lambda: secrets.token_hex(16))
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    resource = Column(String(50))  # Resource type (case, evidence, user, etc.)
    action = Column(String(50))    # Action (create, read, update, delete, etc.)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def to_dict(self) -> Dict:
        """Convert permission to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action
        }

class ActivityLog(Base):
    """Activity logging for audit trail"""
    __tablename__ = 'activity_logs'
    
    id = Column(String, primary_key=True, default=lambda: secrets.token_hex(16))
    user_id = Column(String, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String)
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    @classmethod
    def log(cls, user_id: str, action: str, resource_type: str = None,
            resource_id: str = None, details: Dict = None, success: bool = True):
        """Create an activity log entry"""
        return cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            success=success
        )
    
    def to_dict(self) -> Dict:
        """Convert activity log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'success': self.success
        }

class Case(Base):
    """Case model for demonstration (extend as needed)"""
    __tablename__ = 'cases'
    
    id = Column(String, primary_key=True, default=lambda: secrets.token_hex(16))
    case_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(200))
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, COLD, ARCHIVED
    sensitivity = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assigned_users = relationship("User", secondary=user_cases, back_populates="assigned_cases")