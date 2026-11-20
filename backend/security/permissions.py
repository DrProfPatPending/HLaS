# Base club role (CORE-35, #62). Every club member holds it as an explicit,
# club-scoped assignment, granted and revoked automatically from membership
# (see db.postgres_backend.sync_member_roles) with an admin override.
# Committee and admin roles are layered on top of it. Nothing grants it by
# default: no role means no permissions. The only exception is the
# non-PostgreSQL fallback mode, which has no RBAC tables (auth.principal).
MEMBER_ROLE_CODE = 'member'

ROLE_CODES = (
    'member',
    'committee',
    'club_admin',
    'club_manager',
    'app_admin',
    'app_owner',
)

ROLE_HIERARCHY = {
    'member': {'member'},
    'committee': {'member', 'committee'},
    'club_admin': {'member', 'club_admin'},
    'club_manager': {'member', 'club_admin', 'club_manager'},
    'app_admin': {'member', 'club_admin', 'club_manager', 'app_admin'},
    'app_owner': {'member', 'club_admin', 'club_manager', 'app_admin', 'app_owner'},
}

PERMISSIONS = {
    'member.self.read': {'member', 'committee', 'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'member.self.update': {'member', 'committee', 'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'member.club.list': {'committee', 'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'member.club.create': {'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'member.club.update': {'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'member.club.delete': {'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'club.read': {'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'club.update': {'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'club.create': {'app_admin', 'app_owner'},
    'club.delete': {'app_admin', 'app_owner'},
    'smtp.club.manage': {'club_manager', 'app_admin', 'app_owner'},
    'newsletter.send': {'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'document.club.manage': {'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'field_order.club.manage': {'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'role.assign.club': {'app_admin', 'app_owner'},
    'role.assign.global': {'app_owner'},
    'system.settings': {'app_owner'},
    'backup.create': {'app_admin', 'app_owner'},
    'backup.read': {'app_admin', 'app_owner'},
    'backup.download': {'app_admin', 'app_owner'},
    'backup.delete': {'app_admin', 'app_owner'},
}


def expand_role_codes(role_codes):
    expanded = set()
    for role_code in (role_codes or set()):
        expanded.update(ROLE_HIERARCHY.get(str(role_code), {str(role_code)}))
    return expanded


def has_permission(role_codes, permission):
    allowed_roles = PERMISSIONS.get(str(permission), set())
    if not allowed_roles:
        return False
    effective_roles = expand_role_codes(set(role_codes or set()))
    return bool(effective_roles.intersection(allowed_roles))


def list_permissions(role_codes):
    effective_roles = expand_role_codes(set(role_codes or set()))
    granted = []
    for permission, allowed_roles in PERMISSIONS.items():
        if effective_roles.intersection(allowed_roles):
            granted.append(permission)
    return sorted(granted)
