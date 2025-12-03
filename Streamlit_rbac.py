"""
Streamlit RBAC Authentication System
For Crime Investigation Graph Application
"""

import streamlit as st
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import secrets
import sqlite3
from enum import Enum

class Role(Enum):
    """User roles for the system"""
    ADMIN = "admin"
    CHIEF_OFFICER = "chief_officer"
    DETECTIVE = "detective"
    POLICE_OFFICER = "police_officer"

class Permission(Enum):
    """System permissions"""
    # Dashboard
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_FULL_STATS = "view_full_stats"
    
    # AI Assistant
    USE_AI_ASSISTANT = "use_ai_assistant"
    VIEW_AI_HISTORY = "view_ai_history"
    
    # Graph Operations
    VIEW_GRAPH = "view_graph"
    RUN_ALGORITHMS = "run_algorithms"
    MODIFY_GRAPH = "modify_graph"
    
    # Network Visualization
    VIEW_NETWORK = "view_network"
    EXPORT_NETWORK = "export_network"
    
    # Geographic Mapping
    VIEW_MAP = "view_map"
    VIEW_SENSITIVE_LOCATIONS = "view_sensitive_locations"
    
    # Case Management
    VIEW_CASES = "view_cases"
    CREATE_CASES = "create_cases"
    EDIT_CASES = "edit_cases"
    DELETE_CASES = "delete_cases"
    
    # User Management
    MANAGE_USERS = "manage_users"
    VIEW_LOGS = "view_logs"

class StreamlitRBAC:
    """RBAC system for Streamlit applications"""
    
    # Role-Permission Mapping
    ROLE_PERMISSIONS = {
        Role.ADMIN: [p for p in Permission],  # All permissions
        
        Role.CHIEF_OFFICER: [
            Permission.VIEW_DASHBOARD,
            Permission.VIEW_FULL_STATS,
            Permission.USE_AI_ASSISTANT,
            Permission.VIEW_AI_HISTORY,
            Permission.VIEW_GRAPH,
            Permission.RUN_ALGORITHMS,
            Permission.VIEW_NETWORK,
            Permission.EXPORT_NETWORK,
            Permission.VIEW_MAP,
            Permission.VIEW_SENSITIVE_LOCATIONS,
            Permission.VIEW_CASES,
            Permission.CREATE_CASES,
            Permission.EDIT_CASES,
            Permission.VIEW_LOGS
        ],
        
        Role.DETECTIVE: [
            Permission.VIEW_DASHBOARD,
            Permission.VIEW_FULL_STATS,
            Permission.USE_AI_ASSISTANT,
            Permission.VIEW_GRAPH,
            Permission.RUN_ALGORITHMS,
            Permission.VIEW_NETWORK,
            Permission.VIEW_MAP,
            Permission.VIEW_CASES,
            Permission.CREATE_CASES,
            Permission.EDIT_CASES
        ],
        
        Role.POLICE_OFFICER: [
            Permission.VIEW_DASHBOARD,
            Permission.USE_AI_ASSISTANT,
            Permission.VIEW_GRAPH,
            Permission.VIEW_NETWORK,
            Permission.VIEW_MAP,
            Permission.VIEW_CASES
        ]
    }
    
    def __init__(self, db_path: str = "rbac_users.db"):
        """Initialize RBAC system"""
        self.db_path = db_path
        self.init_database()
        self.create_default_users()
    
    def init_database(self):
        """Initialize user database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                badge_number TEXT,
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Activity logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_default_users(self):
        """Create default test users"""
        default_users = [
            {
                'username': 'admin',
                'password': 'Admin@123456',
                'role': Role.ADMIN.value,
                'first_name': 'System',
                'last_name': 'Administrator',
                'badge_number': 'ADM001',
                'department': 'Administration'
            },
            {
                'username': 'chief_anderson',
                'password': 'Chief@123456',
                'role': Role.CHIEF_OFFICER.value,
                'first_name': 'Michael',
                'last_name': 'Anderson',
                'badge_number': 'CHF001',
                'department': 'Criminal Investigation'
            },
            {
                'username': 'detective_smith',
                'password': 'Detective@123456',
                'role': Role.DETECTIVE.value,
                'first_name': 'Sarah',
                'last_name': 'Smith',
                'badge_number': 'DET002',
                'department': 'Homicide'
            },
            {
                'username': 'officer_brown',
                'password': 'Officer@123456',
                'role': Role.POLICE_OFFICER.value,
                'first_name': 'James',
                'last_name': 'Brown',
                'badge_number': 'OFF003',
                'department': 'Patrol'
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for user in default_users:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO users 
                    (username, password_hash, role, first_name, last_name, badge_number, department)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user['username'],
                    self.hash_password(user['password']),
                    user['role'],
                    user['first_name'],
                    user['last_name'],
                    user['badge_number'],
                    user['department']
                ))
            except sqlite3.IntegrityError:
                pass  # User already exists
        
        conn.commit()
        conn.close()
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, role, first_name, last_name, badge_number, department, is_active
            FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, self.hash_password(password)))
        
        user = cursor.fetchone()
        
        if user and user[7]:  # Check if user exists and is active
            # Update last login
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                         (datetime.now(), user[0]))
            
            # Log activity
            cursor.execute('INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
                         (user[0], 'login', f'User {username} logged in'))
            
            conn.commit()
            conn.close()
            
            return {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'first_name': user[3],
                'last_name': user[4],
                'badge_number': user[5],
                'department': user[6],
                'permissions': [p.value for p in self.ROLE_PERMISSIONS.get(Role(user[2]), [])]
            }
        
        conn.close()
        return None
    
    def has_permission(self, user_role: str, permission: Permission) -> bool:
        """Check if role has permission"""
        role_enum = Role(user_role)
        return permission in self.ROLE_PERMISSIONS.get(role_enum, [])
    
    def log_activity(self, user_id: int, action: str, details: str = ""):
        """Log user activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
                      (user_id, action, details))
        
        conn.commit()
        conn.close()
    
    def get_activity_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent activity logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.*, u.username 
            FROM activity_logs l
            JOIN users u ON l.user_id = u.id
            ORDER BY l.timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': log[0],
                'user_id': log[1],
                'action': log[2],
                'details': log[3],
                'timestamp': log[4],
                'username': log[5]
            }
            for log in logs
        ]
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, role, first_name, last_name, badge_number, department, 
                   created_at, last_login, is_active
            FROM users
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'first_name': user[3],
                'last_name': user[4],
                'badge_number': user[5],
                'department': user[6],
                'created_at': user[7],
                'last_login': user[8],
                'is_active': user[9]
            }
            for user in users
        ]

def init_rbac():
    """Initialize RBAC system in session state"""
    if 'rbac' not in st.session_state:
        st.session_state.rbac = StreamlitRBAC()
    return st.session_state.rbac

def require_login():
    """Decorator to require login for pages"""
    if 'user' not in st.session_state:
        st.warning("⚠️ Please login to access this page")
        st.stop()

def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'user' not in st.session_state:
                st.warning("⚠️ Please login to access this feature")
                st.stop()
            
            user = st.session_state.user
            rbac = init_rbac()
            
            if not rbac.has_permission(user['role'], permission):
                st.error(f"🚫 Access Denied: You need {permission.value} permission")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def render_login_page():
    """Render login page"""
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .test-users {
            background: rgba(102, 126, 234, 0.1);
            padding: 1rem;
            border-radius: 10px;
            margin-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🔒 Login</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Crime Investigation Graph System</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_button = st.form_submit_button("🔓 Login", use_container_width=True, type="primary")
            with col_b:
                if st.form_submit_button("ℹ️ Show Test Users", use_container_width=True):
                    st.session_state.show_test_users = not st.session_state.get('show_test_users', False)
            
            if login_button:
                if username and password:
                    rbac = init_rbac()
                    user = rbac.authenticate(username, password)
                    
                    if user:
                        st.session_state.user = user
                        st.success(f"✅ Welcome, {user['first_name']} {user['last_name']}!")
                        rbac.log_activity(user['id'], 'page_view', 'Dashboard')
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
        
        if st.session_state.get('show_test_users', False):
            st.markdown("### 🧪 Test Users")
            
            test_users = [
                ("👨‍💼 **Admin**", "admin / Admin@123456", "Full system access"),
                ("👮 **Chief Officer**", "chief_anderson / Chief@123456", "Department management"),
                ("🕵️ **Detective**", "detective_smith / Detective@123456", "Investigation access"),
                ("👮‍♂️ **Police Officer**", "officer_brown / Officer@123456", "Basic access")
            ]
            
            for title, creds, desc in test_users:
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin: 8px 0;'>
                    {title}<br/>
                    <code style='color: #667eea;'>{creds}</code><br/>
                    <small style='color: #94a3b8;'>{desc}</small>
                </div>
                """, unsafe_allow_html=True)

def render_user_menu():
    """Render user menu in sidebar"""
    if 'user' in st.session_state:
        user = st.session_state.user
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Profile")
        
        # User info
        st.sidebar.markdown(f"""
        <div style='background: rgba(102, 126, 234, 0.1); padding: 10px; border-radius: 8px;'>
            <strong>{user['first_name']} {user['last_name']}</strong><br/>
            <small style='color: #94a3b8;'>@{user['username']}</small><br/>
            <small style='color: #667eea;'>{user['role'].replace('_', ' ').title()}</small><br/>
            <small>Badge: {user['badge_number']}</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown("")
        
        # Logout button
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            rbac = init_rbac()
            rbac.log_activity(user['id'], 'logout', 'User logged out')
            del st.session_state.user
            st.rerun()
        
        # Admin panel
        if user['role'] == Role.ADMIN.value:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### ⚙️ Admin Panel")
            
            if st.sidebar.button("👥 Manage Users", use_container_width=True):
                st.session_state.page = 'User Management'
                st.rerun()
            
            if st.sidebar.button("📋 View Logs", use_container_width=True):
                st.session_state.page = 'Activity Logs'
                st.rerun()

def check_page_permission(page: str) -> bool:
    """Check if user has permission to access page"""
    if 'user' not in st.session_state:
        return False
    
    rbac = init_rbac()
    user_role = st.session_state.user['role']
    
    # Page permission mapping
    page_permissions = {
        'Dashboard': Permission.VIEW_DASHBOARD,
        'AI Assistant': Permission.USE_AI_ASSISTANT,
        'Graph Algorithms': Permission.RUN_ALGORITHMS,
        'Network Visualization': Permission.VIEW_NETWORK,
        'Geographic Mapping': Permission.VIEW_MAP,
        'User Management': Permission.MANAGE_USERS,
        'Activity Logs': Permission.VIEW_LOGS
    }
    
    required_permission = page_permissions.get(page)
    if required_permission:
        return rbac.has_permission(user_role, required_permission)
    
    return True