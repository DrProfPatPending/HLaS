import uuid

from flask import request

_admin_tokens = set()


def issue_admin_token():
    token = str(uuid.uuid4())
    _admin_tokens.add(token)
    return token


def require_admin_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    return auth_header[7:] in _admin_tokens


def revoke_admin_token_from_request():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        _admin_tokens.discard(auth_header[7:])
