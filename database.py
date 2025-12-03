from neo4j import GraphDatabase
import config

class Database:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def query(self, cypher, params=None):
        with self.driver.session() as session:
            result = session.run(cypher, params or {})
            return [dict(record) for record in result]
    
    def clear_all(self):
        self.query("MATCH (n) DETACH DELETE n")
        print("🗑️  Database cleared")


"""
Database Setup and Initialization
Initialize database, create tables, and seed initial data
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, User, Role, Permission, Case
from RBAC_config import RolePermissions, Role as RoleEnum, Permission as PermissionEnum
import os
import secrets

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///crime_investigation.db')

# Create database engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
session_factory = sessionmaker(bind=engine)
db_session = scoped_session(session_factory)

def init_database():
    """Initialize database and create all tables"""
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

def seed_roles_and_permissions():
    """Seed initial roles and permissions"""
    print("Seeding roles and permissions...")
    
    # Create all permissions
    for perm in PermissionEnum:
        permission = db_session.query(Permission).filter_by(name=perm.value).first()
        if not permission:
            # Parse resource and action from permission name
            parts = perm.value.split('_')
            if len(parts) >= 2:
                action = parts[0]  # create, view, update, delete, etc.
                resource = '_'.join(parts[1:])  # case, evidence, user, etc.
            else:
                action = perm.value
                resource = 'system'
            
            permission = Permission(
                name=perm.value,
                description=f"Permission to {perm.value.replace('_', ' ')}",
                resource=resource,
                action=action
            )
            db_session.add(permission)
    
    db_session.commit()
    
    # Create all roles
    for role_enum in RoleEnum:
        role = db_session.query(Role).filter_by(name=role_enum.value).first()
        if not role:
            hierarchy = RolePermissions.get_role_hierarchy()
            priority = hierarchy.get(role_enum, 0)
            
            role = Role(
                name=role_enum.value,
                description=f"{role_enum.value.replace('_', ' ').title()} role",
                priority=priority
            )
            db_session.add(role)
            db_session.commit()
            
            # Assign permissions to role
            role_permissions = RolePermissions.get_permissions(role_enum)
            for perm_enum in role_permissions:
                permission = db_session.query(Permission).filter_by(name=perm_enum.value).first()
                if permission and permission not in role.permissions:
                    role.permissions.append(permission)
    
    db_session.commit()
    print(f"Created {len(list(RoleEnum))} roles and {len(list(PermissionEnum))} permissions")

def create_default_admin():
    """Create a default admin user"""
    print("Creating default admin user...")
    
    # Check if admin already exists
    admin = db_session.query(User).filter_by(username='admin').first()
    if admin:
        print("Admin user already exists")
        return admin
    
    # Create admin user
    admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@123456')
    admin = User(
        username='admin',
        email='admin@crimeinvestigation.local',
        password=admin_password,
        first_name='System',
        last_name='Administrator',
        badge_number='ADMIN001',
        department='System Administration',
        is_active=True,
        is_verified=True
    )
    
    # Assign admin role
    admin_role = db_session.query(Role).filter_by(name='admin').first()
    if admin_role:
        admin.roles.append(admin_role)
    
    db_session.add(admin)
    db_session.commit()
    
    print(f"Admin user created successfully")
    print(f"Username: admin")
    print(f"Password: {admin_password}")
    print("⚠️  Please change the admin password after first login!")
    
    return admin

def create_sample_users():
    """Create sample users for testing"""
    print("Creating sample users...")
    
    sample_users = [
        {
            'username': 'chief_anderson',
            'email': 'chief.anderson@police.local',
            'password': 'Chief@123456',
            'first_name': 'Michael',
            'last_name': 'Anderson',
            'badge_number': 'CHF001',
            'department': 'Criminal Investigation',
            'role': 'chief_officer'
        },
        {
            'username': 'detective_smith',
            'email': 'detective.smith@police.local',
            'password': 'Detective@123456',
            'first_name': 'Sarah',
            'last_name': 'Smith',
            'badge_number': 'DET002',
            'department': 'Homicide',
            'role': 'detective'
        },
        {
            'username': 'detective_jones',
            'email': 'detective.jones@police.local',
            'password': 'Detective@123456',
            'first_name': 'Robert',
            'last_name': 'Jones',
            'badge_number': 'DET003',
            'department': 'Robbery',
            'role': 'detective'
        },
        {
            'username': 'officer_brown',
            'email': 'officer.brown@police.local',
            'password': 'Officer@123456',
            'first_name': 'James',
            'last_name': 'Brown',
            'badge_number': 'OFF004',
            'department': 'Patrol',
            'role': 'police_officer'
        },
        {
            'username': 'officer_davis',
            'email': 'officer.davis@police.local',
            'password': 'Officer@123456',
            'first_name': 'Emily',
            'last_name': 'Davis',
            'badge_number': 'OFF005',
            'department': 'Patrol',
            'role': 'police_officer'
        }
    ]
    
    created_users = []
    for user_data in sample_users:
        # Check if user already exists
        existing_user = db_session.query(User).filter_by(username=user_data['username']).first()
        if existing_user:
            print(f"User {user_data['username']} already exists")
            continue
        
        # Create user
        role_name = user_data.pop('role')
        user = User(**user_data, is_active=True, is_verified=True)
        
        # Assign role
        role = db_session.query(Role).filter_by(name=role_name).first()
        if role:
            user.roles.append(role)
        
        db_session.add(user)
        created_users.append(user)
        print(f"Created user: {user.username} ({role_name})")
    
    db_session.commit()
    return created_users

def create_sample_cases():
    """Create sample cases for testing"""
    print("Creating sample cases...")
    
    sample_cases = [
        {
            'case_number': 'CAS-2024-001',
            'title': 'Downtown Robbery Investigation',
            'status': 'OPEN',
            'sensitivity': 'HIGH'
        },
        {
            'case_number': 'CAS-2024-002',
            'title': 'Vandalism at City Park',
            'status': 'OPEN',
            'sensitivity': 'LOW'
        },
        {
            'case_number': 'CAS-2024-003',
            'title': 'Identity Theft Ring',
            'status': 'OPEN',
            'sensitivity': 'MEDIUM'
        },
        {
            'case_number': 'CAS-2023-099',
            'title': 'Cold Case - Missing Person',
            'status': 'COLD',
            'sensitivity': 'HIGH'
        }
    ]
    
    created_cases = []
    for case_data in sample_cases:
        # Check if case already exists
        existing_case = db_session.query(Case).filter_by(case_number=case_data['case_number']).first()
        if existing_case:
            print(f"Case {case_data['case_number']} already exists")
            continue
        
        case = Case(**case_data)
        db_session.add(case)
        created_cases.append(case)
        print(f"Created case: {case.case_number}")
    
    # Assign users to cases
    if created_cases:
        detective = db_session.query(User).filter_by(username='detective_smith').first()
        chief = db_session.query(User).filter_by(username='chief_anderson').first()
        
        if detective and created_cases:
            detective.assigned_cases.extend(created_cases[:2])
        
        if chief and created_cases:
            chief.assigned_cases.extend(created_cases)
    
    db_session.commit()
    return created_cases

def reset_database():
    """Reset database (drop and recreate all tables)"""
    print("⚠️  Resetting database...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped")
    init_database()
    seed_roles_and_permissions()
    create_default_admin()
    create_sample_users()
    create_sample_cases()
    print("✅ Database reset complete")

def get_database_stats():
    """Get database statistics"""
    stats = {
        'users': db_session.query(User).count(),
        'roles': db_session.query(Role).count(),
        'permissions': db_session.query(Permission).count(),
        'cases': db_session.query(Case).count(),
        'active_users': db_session.query(User).filter_by(is_active=True).count(),
    }
    
    print("\n📊 Database Statistics:")
    print(f"  - Users: {stats['users']} ({stats['active_users']} active)")
    print(f"  - Roles: {stats['roles']}")
    print(f"  - Permissions: {stats['permissions']}")
    print(f"  - Cases: {stats['cases']}")
    
    return stats

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        response = input("⚠️  This will delete all data. Are you sure? (yes/no): ")
        if response.lower() == 'yes':
            reset_database()
        else:
            print("Reset cancelled")
    else:
        # Normal initialization
        init_database()
        seed_roles_and_permissions()
        admin = create_default_admin()
        
        # Ask if sample data should be created
        response = input("Create sample users and cases? (yes/no): ")
        if response.lower() == 'yes':
            create_sample_users()
            create_sample_cases()
    
    # Show statistics
    get_database_stats()
    print("\n✅ Database setup complete!")