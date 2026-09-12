from __future__ import annotations

from .models import Permission, Principal, Role


class AuthorizationError(PermissionError):
    pass


class Policy:
    def allows(self, principal: Principal, permission: Permission) -> bool:
        raise NotImplementedError


class RBACPolicy(Policy):
    role_permissions = {
        Role.ADMIN: set(Permission),
        Role.RESEARCHER: {
            Permission.READ,
            Permission.UPLOAD,
            Permission.EXECUTE,
            Permission.EXPORT,
        },
        Role.REVIEWER: {Permission.READ, Permission.REVIEW, Permission.EXPORT},
        Role.JUDGE: {Permission.READ, Permission.JUDGE, Permission.EXPORT},
        Role.VIEWER: {Permission.READ},
    }

    def allows(self, principal: Principal, permission: Permission) -> bool:
        if permission in principal.permissions:
            return True
        return any(
            permission in self.role_permissions.get(role, set())
            for role in principal.roles
        )

    def require(self, principal: Principal, permission: Permission) -> None:
        if not self.allows(principal, permission):
            raise AuthorizationError(f"Permission denied: {permission.value}")
