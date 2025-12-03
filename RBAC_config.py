"""
RBAC Configuration for Crime Investigation Graph System
This module defines roles, permissions, and access control policies
"""

from enum import Enum
from typing import Set, Dict, List

class Role(Enum):
    """Define all system roles"""
    ADMIN = "admin"
    CHIEF_OFFICER = "chief_officer"
    DETECTIVE = "detective"
    POLICE_OFFICER = "police_officer"

class Permission(Enum):
    """Define all system permissions"""
    # Case Management Permissions
    CREATE_CASE = "create_case"
    VIEW_CASE = "view_case"
    UPDATE_CASE = "update_case"
    DELETE_CASE = "delete_case"
    CLOSE_CASE = "close_case"
    REOPEN_CASE = "reopen_case"
    ASSIGN_CASE = "assign_case"
    
    # Evidence Management
    ADD_EVIDENCE = "add_evidence"
    VIEW_EVIDENCE = "view_evidence"
    UPDATE_EVIDENCE = "update_evidence"
    DELETE_EVIDENCE = "delete_evidence"
    VERIFY_EVIDENCE = "verify_evidence"
    
    # Suspect Management
    ADD_SUSPECT = "add_suspect"
    VIEW_SUSPECT = "view_suspect"
    UPDATE_SUSPECT = "update_suspect"
    DELETE_SUSPECT = "delete_suspect"
    
    # Witness Management
    ADD_WITNESS = "add_witness"
    VIEW_WITNESS = "view_witness"
    UPDATE_WITNESS = "update_witness"
    DELETE_WITNESS = "delete_witness"
    
    # Graph Operations
    VIEW_GRAPH = "view_graph"
    CREATE_NODE = "create_node"
    UPDATE_NODE = "update_node"
    DELETE_NODE = "delete_node"
    CREATE_EDGE = "create_edge"
    UPDATE_EDGE = "update_edge"
    DELETE_EDGE = "delete_edge"
    ANALYZE_GRAPH = "analyze_graph"
    EXPORT_GRAPH = "export_graph"
    
    # Report Generation
    GENERATE_REPORT = "generate_report"
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORT = "export_report"
    
    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    RUN_ANALYTICS = "run_analytics"
    EXPORT_ANALYTICS = "export_analytics"
    
    # User Management
    CREATE_USER = "create_user"
    VIEW_USER = "view_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    ASSIGN_ROLE = "assign_role"
    
    # System Administration
    VIEW_LOGS = "view_logs"
    MANAGE_SYSTEM = "manage_system"
    BACKUP_DATA = "backup_data"
    RESTORE_DATA = "restore_data"

class RolePermissions:
    """Define role-permission mappings"""
    
    ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
        Role.ADMIN: set(Permission),  # All permissions
        
        Role.CHIEF_OFFICER: {
            # All case management
            Permission.CREATE_CASE, Permission.VIEW_CASE, Permission.UPDATE_CASE,
            Permission.DELETE_CASE, Permission.CLOSE_CASE, Permission.REOPEN_CASE,
            Permission.ASSIGN_CASE,
            # All evidence management
            Permission.ADD_EVIDENCE, Permission.VIEW_EVIDENCE, Permission.UPDATE_EVIDENCE,
            Permission.DELETE_EVIDENCE, Permission.VERIFY_EVIDENCE,
            # All suspect/witness management
            Permission.ADD_SUSPECT, Permission.VIEW_SUSPECT, Permission.UPDATE_SUSPECT,
            Permission.DELETE_SUSPECT, Permission.ADD_WITNESS, Permission.VIEW_WITNESS,
            Permission.UPDATE_WITNESS, Permission.DELETE_WITNESS,
            # All graph operations
            Permission.VIEW_GRAPH, Permission.CREATE_NODE, Permission.UPDATE_NODE,
            Permission.DELETE_NODE, Permission.CREATE_EDGE, Permission.UPDATE_EDGE,
            Permission.DELETE_EDGE, Permission.ANALYZE_GRAPH, Permission.EXPORT_GRAPH,
            # Reports and analytics
            Permission.GENERATE_REPORT, Permission.VIEW_REPORTS, Permission.EXPORT_REPORT,
            Permission.VIEW_ANALYTICS, Permission.RUN_ANALYTICS, Permission.EXPORT_ANALYTICS,
            # User management (limited)
            Permission.VIEW_USER, Permission.ASSIGN_ROLE,
            # System
            Permission.VIEW_LOGS
        },
        
        Role.DETECTIVE: {
            # Case management
            Permission.CREATE_CASE, Permission.VIEW_CASE, Permission.UPDATE_CASE,
            Permission.CLOSE_CASE, Permission.ASSIGN_CASE,
            # Evidence management
            Permission.ADD_EVIDENCE, Permission.VIEW_EVIDENCE, Permission.UPDATE_EVIDENCE,
            Permission.VERIFY_EVIDENCE,
            # Suspect/witness management
            Permission.ADD_SUSPECT, Permission.VIEW_SUSPECT, Permission.UPDATE_SUSPECT,
            Permission.ADD_WITNESS, Permission.VIEW_WITNESS, Permission.UPDATE_WITNESS,
            # Graph operations
            Permission.VIEW_GRAPH, Permission.CREATE_NODE, Permission.UPDATE_NODE,
            Permission.CREATE_EDGE, Permission.UPDATE_EDGE, Permission.ANALYZE_GRAPH,
            Permission.EXPORT_GRAPH,
            # Reports and analytics
            Permission.GENERATE_REPORT, Permission.VIEW_REPORTS, Permission.EXPORT_REPORT,
            Permission.VIEW_ANALYTICS, Permission.RUN_ANALYTICS,
            # Limited user access
            Permission.VIEW_USER
        },
        
        Role.POLICE_OFFICER: {
            # Basic case management
            Permission.VIEW_CASE, Permission.UPDATE_CASE,
            # Evidence management
            Permission.ADD_EVIDENCE, Permission.VIEW_EVIDENCE,
            # Witness management
            Permission.ADD_WITNESS, Permission.VIEW_WITNESS,
            # View suspects
            Permission.VIEW_SUSPECT,
            # Basic graph operations
            Permission.VIEW_GRAPH, Permission.CREATE_NODE,
            # View reports
            Permission.VIEW_REPORTS,
            Permission.VIEW_ANALYTICS
        }
    }
    
    @classmethod
    def get_permissions(cls, role: Role) -> Set[Permission]:
        """Get all permissions for a given role"""
        return cls.ROLE_PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, role: Role, permission: Permission) -> bool:
        """Check if a role has a specific permission"""
        return permission in cls.get_permissions(role)
    
    @classmethod
    def get_role_hierarchy(cls) -> Dict[Role, int]:
        """Return role hierarchy with priority levels"""
        return {
            Role.ADMIN: 10,
            Role.CHIEF_OFFICER: 8,
            Role.DETECTIVE: 5,
            Role.POLICE_OFFICER: 3
        }

class ResourcePermissions:
    """Define resource-specific permissions"""
    
    @staticmethod
    def can_access_case(user_role: Role, case_status: str, case_sensitivity: str) -> bool:
        """Check if user can access a specific case based on status and sensitivity"""
        hierarchy = RolePermissions.get_role_hierarchy()
        user_level = hierarchy.get(user_role, 0)
        
        # High sensitivity cases require higher clearance
        if case_sensitivity == "HIGH":
            return user_level >= 5  # Detective or above
        elif case_sensitivity == "MEDIUM":
            return user_level >= 3  # Police Officer or above
        else:
            return user_level >= 3  # All authenticated officers can view low sensitivity
    
    @staticmethod
    def can_modify_evidence(user_role: Role, evidence_type: str) -> bool:
        """Check if user can modify specific types of evidence"""
        if evidence_type in ["DNA", "FORENSIC"]:
            # Only Detective and above can modify forensic evidence
            return user_role in [Role.DETECTIVE, Role.CHIEF_OFFICER, Role.ADMIN]
        return RolePermissions.has_permission(user_role, Permission.UPDATE_EVIDENCE)

# Export configuration
RBAC_CONFIG = {
    "roles": [role.value for role in Role],
    "permissions": [perm.value for perm in Permission],
    "role_permissions": {
        role.value: [perm.value for perm in perms]
        for role, perms in RolePermissions.ROLE_PERMISSIONS.items()
    },
    "hierarchy": {role.value: level for role, level in RolePermissions.get_role_hierarchy().items()}
}