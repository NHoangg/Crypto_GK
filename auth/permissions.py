"""Permission definitions and role-based access control."""

from typing import List, Set
from config import ROLES

# Define permissions for each role
ROLE_PERMISSIONS = {
    "Content Creator": {
        "register_document",
        "view_documents",
        "transfer_ownership",
    },
    "Censor": {
        "view_documents",
        "review_document",
        "approve_document",
        "reject_document",
    },
    "Publisher": {
        "view_documents",
        "approve_document",
        "reject_document",
        "transfer_ownership",
    },
    "Customer": {
        "view_documents",
        "verify_document",
        "transfer_ownership",
    },
    "Legal Authority": {
        "view_documents",
        "review_document",
        "approve_document",
        "reject_document",
        "delete_document",
        "delete_all_documents",
        "register_document",
        "transfer_ownership",
        "view_audit_logs",
    },
}


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    if role not in ROLE_PERMISSIONS:
        return False
    return permission in ROLE_PERMISSIONS[role]


def get_allowed_roles_for(permission: str) -> List[str]:
    """Get all roles that have a specific permission."""
    return [role for role, perms in ROLE_PERMISSIONS.items() if permission in perms]


def get_permissions_for_role(role: str) -> Set[str]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())
