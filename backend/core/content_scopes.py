DEFAULT_CONTENT_SCOPE = 'home'
HEALTH_SAFETY_SCOPE = 'health-safety'


def normalize_content_scope(raw_scope, *, allow_all=False):
    value = str(raw_scope or '').strip().lower().replace('_', '-')
    if allow_all and value == 'all':
        return 'all'
    if value in ('health-safety', 'healthandsafety', 'hs'):
        return HEALTH_SAFETY_SCOPE
    return DEFAULT_CONTENT_SCOPE