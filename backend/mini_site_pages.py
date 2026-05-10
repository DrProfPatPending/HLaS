"""
Mini site page definitions and utilities.

Defines the template structure for all available pages and helper functions.
"""

# Available page templates with default configurations
PAGE_TEMPLATES = {
    'home': {
        'id': 'home',
        'type': 'home',
        'title': 'Home',
        'enabled': True,
        'canDisable': False,  # Home page cannot be hidden
        'description': 'Club home page with hero image and welcome message',
    },
    'about': {
        'id': 'about',
        'type': 'about',
        'title': 'About Us',
        'enabled': True,
        'canDisable': True,
        'description': 'Information about your club, history, and mission',
    },
    'waters': {
        'id': 'waters',
        'type': 'waters',
        'title': 'Our Waters',
        'enabled': True,
        'canDisable': True,
        'description': 'Details about your fishing waters, beats, and access information',
    },
    'news': {
        'id': 'news',
        'type': 'news',
        'title': 'News',
        'enabled': True,
        'canDisable': True,
        'description': 'Club news, updates, and announcements',
    },
    'join': {
        'id': 'join',
        'type': 'join',
        'title': 'Join',
        'enabled': True,
        'canDisable': True,
        'description': 'Membership information and how to join',
    },
    'contact': {
        'id': 'contact',
        'type': 'contact',
        'title': 'Contact Us',
        'enabled': True,
        'canDisable': True,
        'description': 'Contact form and club information',
    },
}

DEFAULT_PAGES_CONFIG = [
    PAGE_TEMPLATES['home'],
    PAGE_TEMPLATES['about'],
    PAGE_TEMPLATES['waters'],
    PAGE_TEMPLATES['news'],
    PAGE_TEMPLATES['join'],
    PAGE_TEMPLATES['contact'],
]


def get_default_pages():
    """Get list of default pages with template values."""
    return [dict(page) for page in DEFAULT_PAGES_CONFIG]


def normalize_pages_config(raw_pages, club_name=''):
    """
    Normalize page configuration, ensuring required structure.
    
    Args:
        raw_pages: Raw pages data from API or storage
        club_name: Club name for default text generation
    
    Returns:
        List of normalized page configurations
    """
    if not isinstance(raw_pages, list):
        return get_default_pages()
    
    # Start with template pages
    normalized = {page['id']: dict(page) for page in DEFAULT_PAGES_CONFIG}
    
    # Merge in user config
    for raw_page in raw_pages:
        if not isinstance(raw_page, dict):
            continue
        
        page_id = raw_page.get('id')
        if page_id not in normalized:
            continue
        
        # Update enabled status (but respect canDisable)
        if page_id == 'home':
            normalized[page_id]['enabled'] = True  # Home always enabled
        elif 'enabled' in raw_page:
            normalized[page_id]['enabled'] = bool(raw_page['enabled'])
        
        # Update content fields
        for field in ['content', 'headline', 'body_text']:
            if field in raw_page:
                normalized[page_id][field] = raw_page[field]
    
    return list(normalized.values())


def get_enabled_pages(pages_config):
    """Get only enabled pages from configuration."""
    return [page for page in pages_config if page.get('enabled', True)]
