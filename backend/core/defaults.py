def _default_clubs_config():
    return [
        {
            'fullName': 'TEST',
            'shortName': 'TEST',
            'description': 'Dummy fallback club entry',
            'websiteUrl': 'https://example.com/test',
            'adminEmail': 'admin@test.example.com',
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
