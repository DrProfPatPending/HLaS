"""Shared SMTP connect/login/send with structured logging (CORE-31, #58).

Used by the admin SMTP test email and the newsletter send. Every connection,
TLS, login and send failure is logged as a JSON line on the Flask app logger,
plus successful sends and newsletter batch summaries, so an undelivered email
can be diagnosed from the backend logs. A Message-ID is set on each message
and logged, so a send can be matched in the provider's own logs.

Never logged: the SMTP password, message bodies or subjects. Recipient
addresses are masked (``r***@example.org``).
"""

import json
import logging
import re
import smtplib
import time
from contextlib import contextmanager
from email.utils import make_msgid, parseaddr

from flask import current_app, has_app_context

SMTP_TIMEOUT_SECONDS = 20


def _logger(logger=None):
    if logger is not None:
        return logger
    if has_app_context():
        return current_app.logger
    return logging.getLogger('hlas.smtp')


def mask_email(address):
    """Return ``r***@domain`` for an address, keeping only its first character."""
    _, addr = parseaddr(str(address or ''))
    local, sep, domain = addr.partition('@')
    if not sep or not local:
        return '***'
    return f'{local[0]}***@{domain}'


_ADDRESS_IN_TEXT = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')


def scrub_addresses(text):
    """Mask every email address inside free text, e.g. SMTP rejection messages
    such as ``550 5.1.1 <name@example.org>: Recipient address rejected``."""
    return _ADDRESS_IN_TEXT.sub(lambda match: mask_email(match.group(0)), str(text or ''))


def transport_mode(cfg):
    if cfg.get('useSsl'):
        return 'ssl'
    if cfg.get('useTls'):
        return 'starttls'
    return 'plain'


def _exception_fields(exc):
    fields = {'error_type': type(exc).__name__}
    code = getattr(exc, 'smtp_code', None)
    if code is not None:
        fields['smtp_code'] = code
    response = getattr(exc, 'smtp_error', None)
    if response is not None:
        fields['smtp_response'] = scrub_addresses(
            response.decode('utf-8', 'replace') if isinstance(response, bytes) else str(response)
        )[:500]
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        fields['refused'] = _refused_summary(exc.recipients)
    else:
        fields['error'] = scrub_addresses(str(exc))[:500]
    return fields


def _refused_summary(refused):
    summary = []
    for address, detail in (refused or {}).items():
        code, response = (detail + (None, None))[:2] if isinstance(detail, tuple) else (None, detail)
        if isinstance(response, bytes):
            response = response.decode('utf-8', 'replace')
        summary.append({'recipient': mask_email(address), 'smtp_code': code, 'smtp_response': scrub_addresses(response)[:200]})
    return summary


def _log(logger, level, event, base, **fields):
    payload = {'event': event, **base, **fields}
    logger.log(level, json.dumps(payload, default=str))


@contextmanager
def smtp_connection(cfg, *, club, purpose, logger=None):
    """Open, secure and log in to the club's SMTP server; yields the client.

    Failures are logged (``smtp.connect_failed``, ``smtp.tls_failed``,
    ``smtp.auth_failed``) and re-raised unchanged, so callers keep their
    existing error responses. A failure when closing the connection is only
    logged (``smtp.quit_failed``): by then the messages have been sent.
    """
    log = _logger(logger)
    base = {
        'club': club,
        'purpose': purpose,
        'host': cfg.get('host', ''),
        'port': cfg.get('port'),
        'mode': transport_mode(cfg),
    }
    started = time.monotonic()
    try:
        if cfg.get('useSsl'):
            server = smtplib.SMTP_SSL(cfg['host'], cfg['port'], timeout=SMTP_TIMEOUT_SECONDS)
        else:
            server = smtplib.SMTP(cfg['host'], cfg['port'], timeout=SMTP_TIMEOUT_SECONDS)
    except Exception as exc:
        _log(log, logging.ERROR, 'smtp.connect_failed', base, **_exception_fields(exc))
        raise

    try:
        if base['mode'] == 'starttls':
            try:
                server.starttls()
            except Exception as exc:
                _log(log, logging.ERROR, 'smtp.tls_failed', base, **_exception_fields(exc))
                raise
        if cfg.get('username'):
            try:
                server.login(cfg['username'], cfg.get('password', ''))
            except Exception as exc:
                _log(log, logging.ERROR, 'smtp.auth_failed', base, **_exception_fields(exc))
                raise
        _log(log, logging.DEBUG, 'smtp.connected', base, elapsed_ms=round((time.monotonic() - started) * 1000))
        yield server
    finally:
        try:
            server.quit()
        except Exception as exc:
            _log(log, logging.WARNING, 'smtp.quit_failed', base, **_exception_fields(exc))
            try:
                server.close()
            except Exception:
                pass


def send_message(server, message, *, club, purpose, member_id=None, success_level=logging.INFO, logger=None):
    """Send one message, logging the outcome; returns its Message-ID.

    Sets a Message-ID on the From domain if the message has none. Errors are
    logged as ``smtp.send_failed`` and re-raised. Success is logged as
    ``smtp.sent`` at ``success_level`` (newsletters pass DEBUG and log a
    batch summary instead).
    """
    log = _logger(logger)
    if not message['Message-ID']:
        _, from_addr = parseaddr(str(message['From'] or ''))
        domain = from_addr.partition('@')[2] or None
        message['Message-ID'] = make_msgid(domain=domain)
    base = {
        'club': club,
        'purpose': purpose,
        'message_id': message['Message-ID'],
        'recipient': mask_email(message['To']),
    }
    if member_id not in (None, ''):
        base['member_id'] = str(member_id)
    try:
        refused = server.send_message(message)
    except Exception as exc:
        _log(log, logging.ERROR, 'smtp.send_failed', base, **_exception_fields(exc))
        raise
    fields = {'refused': _refused_summary(refused)} if refused else {}
    _log(log, success_level, 'smtp.sent', base, **fields)
    return message['Message-ID']


def log_batch_summary(*, club, purpose, sent, failed, total, logger=None, **extra):
    """One INFO line per newsletter send with the overall counts."""
    level = logging.WARNING if failed else logging.INFO
    _log(_logger(logger), level, 'smtp.batch_summary', {'club': club, 'purpose': purpose},
         total=total, sent=sent, failed=failed, **extra)
