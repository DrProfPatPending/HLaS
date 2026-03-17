def _default_clubs_config():
    return [
        {
            'fullName': 'GAAFFS',
            'shortName': 'GAAFFS',
            'description': 'GAAFFS fishing club members',
            'websiteUrl': 'https://example.com/gaaffs',
            'adminEmail': 'admin@gaaffs.example.com',
            'logoUrl': '',
            'beats': [],
        },
        {
            'fullName': 'CTC',
            'shortName': 'CTC',
            'description': 'CTC fishing club members',
            'websiteUrl': 'https://example.com/ctc',
            'adminEmail': 'admin@ctc.example.com',
            'logoUrl': '',
            'beats': [],
        },
    ]


def _default_server_config():
    return {
        'server': {
            'host': '127.0.0.1',
            'port': 5050,
            'url': 'http://127.0.0.1:5050',
        },
        'tls': {
            'enabled': False,
            'adhoc': True,
            'certFile': '',
            'keyFile': '',
        },
        'startup': {
            'delayMs': 3000,
        },
        'runtime': {
            'debug': False,
            'useReloader': False,
        },
        'logging': {
            'level': 'INFO',
        },
    }
