DEFAULT_ROLE_CODE = 'user'

ROLE_CODES = (
    'user',
    'club_admin',
    'club_manager',
    'app_admin',
    'app_owner',
)

ROLE_HIERARCHY = {
    'user': {'user'},
    'club_admin': {'user', 'club_admin'},
    'club_manager': {'user', 'club_admin', 'club_manager'},
    'app_admin': {'user', 'club_admin', 'club_manager', 'app_admin'},
    'app_owner': {'user', 'club_admin', 'club_manager', 'app_admin', 'app_owner'},
}

PERMISSIONS = {
    'member.self.read': {'user', 'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'member.self.update': {'user', 'club_admin', 'club_manager', 'app_admin', 'app_owner'},
    'member.club.list': {'club_admin', 'club_manager', 'app_admin', 'app_owner'},
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
    if not expanded:
        expanded.add(DEFAULT_ROLE_CODE)
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
