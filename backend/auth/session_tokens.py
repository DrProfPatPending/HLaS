import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from flask import g, jsonify, request
from sqlalchemy import and_, select

from db import get_postgres_backend, is_postgres_reads_enabled

_member_tokens_fallback = {}
_member_refresh_tokens_fallback = {}

MEMBER_TOKEN_TTL_SECONDS = int(os.getenv('HLAS_MEMBER_TOKEN_TTL_SECONDS', '43200'))
MEMBER_REFRESH_TOKEN_TTL_SECONDS = int(os.getenv('HLAS_MEMBER_REFRESH_TOKEN_TTL_SECONDS', str(60 * 60 * 24 * 30)))


def _hash_member_token(raw_token):
    return hashlib.sha256(str(raw_token or '').encode('utf-8')).hexdigest()


def _utcnow():
    return datetime.now(timezone.utc)


def _member_token_expiry():
    return _utcnow() + timedelta(seconds=max(60, MEMBER_TOKEN_TTL_SECONDS))


def _member_refresh_token_expiry():
    return _utcnow() + timedelta(seconds=max(300, MEMBER_REFRESH_TOKEN_TTL_SECONDS))


def extract_bearer_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return ''
    return auth_header[7:].strip()


def issue_member_session_token(member_id, club_short_name, username, user_id=None):
    token_value = secrets.token_urlsafe(32)
    token_hash = _hash_member_token(token_value)
    expires_at = _member_token_expiry()

    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            session.execute(
                backend['member_sessions_table'].insert().values(
                    token_hash=token_hash,
                    user_id=_safe_int(user_id),
                    member_id=int(member_id),
                    club_short_name=str(club_short_name or '').strip(),
                    username=str(username or '').strip(),
                    expires_at=expires_at,
                    last_seen_at=_utcnow(),
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        _member_tokens_fallback[token_hash] = {
            'user_id': _safe_int(user_id),
            'member_id': int(member_id),
            'club_short_name': str(club_short_name or '').strip(),
            'username': str(username or '').strip(),
            'expires_at': expires_at,
            'revoked_at': None,
            'last_seen_at': _utcnow(),
        }

    return token_value


def issue_member_refresh_token(member_id, club_short_name, username, user_id=None):
    token_value = secrets.token_urlsafe(48)
    token_hash = _hash_member_token(token_value)
    expires_at = _member_refresh_token_expiry()

    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            session.execute(
                backend['member_refresh_sessions_table'].insert().values(
                    refresh_token_hash=token_hash,
                    user_id=_safe_int(user_id),
                    member_id=int(member_id),
                    club_short_name=str(club_short_name or '').strip(),
                    username=str(username or '').strip(),
                    expires_at=expires_at,
                    last_seen_at=_utcnow(),
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        _member_refresh_tokens_fallback[token_hash] = {
            'user_id': _safe_int(user_id),
            'member_id': int(member_id),
            'club_short_name': str(club_short_name or '').strip(),
            'username': str(username or '').strip(),
            'expires_at': expires_at,
            'revoked_at': None,
            'last_seen_at': _utcnow(),
        }

    return token_value


def revoke_member_refresh_token(token_value):
    token_hash = _hash_member_token(token_value)
    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            session.execute(
                backend['member_refresh_sessions_table'].update().where(
                    backend['member_refresh_sessions_table'].c.refresh_token_hash == token_hash
                ).values(revoked_at=_utcnow())
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        row = _member_refresh_tokens_fallback.get(token_hash)
        if row is not None:
            row['revoked_at'] = _utcnow()


def get_member_refresh_session_from_token(token_value):
    token_hash = _hash_member_token(token_value)
    now_value = _utcnow()
    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            row = session.execute(
                select(backend['member_refresh_sessions_table']).where(
                    and_(
                        backend['member_refresh_sessions_table'].c.refresh_token_hash == token_hash,
                        backend['member_refresh_sessions_table'].c.revoked_at.is_(None),
                        backend['member_refresh_sessions_table'].c.expires_at > now_value,
                    )
                )
            ).fetchone()
            if row is None:
                return None

            session.execute(
                backend['member_refresh_sessions_table'].update().where(
                    backend['member_refresh_sessions_table'].c.refresh_token_hash == token_hash
                ).values(last_seen_at=now_value)
            )
            session.commit()
            return {
                'user_id': _safe_int(getattr(row, 'user_id', None)),
                'member_id': row.member_id,
                'club_short_name': row.club_short_name,
                'username': row.username,
            }
        finally:
            session.close()

    row = _member_refresh_tokens_fallback.get(token_hash)
    if row is None:
        return None
    if row.get('revoked_at') is not None:
        return None
    if row.get('expires_at') is None or row['expires_at'] <= now_value:
        return None
    row['last_seen_at'] = now_value
    return {
        'user_id': _safe_int(row.get('user_id')),
        'member_id': row.get('member_id'),
        'club_short_name': row.get('club_short_name', ''),
        'username': row.get('username', ''),
    }


def issue_member_token_pair(member_id, club_short_name, username, user_id=None):
    access_token = issue_member_session_token(member_id, club_short_name, username, user_id=user_id)
    refresh_token = issue_member_refresh_token(member_id, club_short_name, username, user_id=user_id)
    return {
        'token': access_token,
        'refreshToken': refresh_token,
        'expiresInSeconds': MEMBER_TOKEN_TTL_SECONDS,
        'refreshExpiresInSeconds': MEMBER_REFRESH_TOKEN_TTL_SECONDS,
    }


def revoke_member_session_token(token_value):
    token_hash = _hash_member_token(token_value)
    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            session.execute(
                backend['member_sessions_table'].update().where(
                    backend['member_sessions_table'].c.token_hash == token_hash
                ).values(revoked_at=_utcnow())
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        row = _member_tokens_fallback.get(token_hash)
        if row is not None:
            row['revoked_at'] = _utcnow()


def get_member_session_from_token(token_value):
    token_hash = _hash_member_token(token_value)
    now_value = _utcnow()
    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            row = session.execute(
                select(backend['member_sessions_table']).where(
                    and_(
                        backend['member_sessions_table'].c.token_hash == token_hash,
                        backend['member_sessions_table'].c.revoked_at.is_(None),
                        backend['member_sessions_table'].c.expires_at > now_value,
                    )
                )
            ).fetchone()
            if row is None:
                return None

            session.execute(
                backend['member_sessions_table'].update().where(
                    backend['member_sessions_table'].c.token_hash == token_hash
                ).values(last_seen_at=now_value)
            )
            session.commit()
            return {
                'user_id': _safe_int(getattr(row, 'user_id', None)),
                'member_id': row.member_id,
                'club_short_name': row.club_short_name,
                'username': row.username,
            }
        finally:
            session.close()

    row = _member_tokens_fallback.get(token_hash)
    if row is None:
        return None
    if row.get('revoked_at') is not None:
        return None
    if row.get('expires_at') is None or row['expires_at'] <= now_value:
        return None
    row['last_seen_at'] = now_value
    return {
        'user_id': _safe_int(row.get('user_id')),
        'member_id': row.get('member_id'),
        'club_short_name': row.get('club_short_name', ''),
        'username': row.get('username', ''),
    }


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def require_member_token_for_club(club_short_name):
    token_value = extract_bearer_token()
    if not token_value:
        return jsonify({'error': 'Unauthorized'}), 401

    session_payload = get_member_session_from_token(token_value)
    if session_payload is None:
        return jsonify({'error': 'Unauthorized'}), 401

    expected = str(club_short_name or '').strip()
    actual = str(session_payload.get('club_short_name', '')).strip()
    if expected and actual and expected != actual:
        return jsonify({'error': 'Forbidden for selected club'}), 403

    g.member_session = session_payload
    return None
