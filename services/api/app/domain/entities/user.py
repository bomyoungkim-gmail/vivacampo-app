from enum import Enum


class UserRole(str, Enum):
    SYSTEM_ADMIN = "system_admin"
    TENANT_ADMIN = "tenant_admin"
    EDITOR = "editor"
    VIEWER = "viewer"
