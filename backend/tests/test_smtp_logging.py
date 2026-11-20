"""CORE-31 (#58): SMTP sends and failures are logged, without secrets."""
import json
import logging
import smtplib
import socket
import unittest
from email.message import EmailMessage
from unittest import mock

from flask import Flask
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import registry, sessionmaker

from core import smtp_send
from routes.admin_routes import create_admin_blueprint
from routes.newsletter_routes import create_newsletter_blueprint

PASSWORD = 'xsmtpsib-not-a-real-key-123'
SMTP_CFG = {
    'host': 'smtp.example.org', 'port': 587, 'username': 'relay-user', 'password': PASSWORD,
    'fromEmail': 'committee@club.example', 'fromName': 'Club', 'useSsl': False, 'useTls': True,
}


class _MockDeps(dict):
    def __missing__(self, key):
        value = mock.MagicMock(name=key)
        self[key] = value
        return value


def _events(log_context):
    """The structured smtp.* events, ignoring the routes' other log lines."""
    events = []
    for record in log_context.records:
        try:
            payload = json.loads(record.getMessage())
        except ValueError:
            continue
        if str(payload.get('event', '')).startswith('smtp.'):
            events.append(payload)
    return events


def _fake_smtp(**behaviour):
    """A MagicMock SMTP client; behaviour maps method name -> side_effect."""
    client = mock.MagicMock(name='smtp-client')
    for method, effect in behaviour.items():
        getattr(client, method).side_effect = effect
    client.send_message.return_value = behaviour.get('refused', {}) if 'send_message' not in behaviour else None
    return client


class SmtpHelperTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.addCleanup(self.ctx.pop)

    def _message(self, to='robert@members.example'):
        message = EmailMessage()
        message['Subject'] = 'Secret subject'
        message['From'] = 'Club <committee@club.example>'
        message['To'] = to
        message.set_content('Private body text')
        return message

    def _assert_no_secrets(self, log_context):
        output = '\n'.join(record.getMessage() for record in log_context.records)
        for secret in (PASSWORD, 'Private body text', 'Secret subject', 'robert@members.example'):
            self.assertNotIn(secret, output)

    def test_mask_email(self):
        self.assertEqual(smtp_send.mask_email('robert@members.example'), 'r***@members.example')
        self.assertEqual(smtp_send.mask_email('Rob <robert@members.example>'), 'r***@members.example')
        self.assertEqual(smtp_send.mask_email(''), '***')
        self.assertEqual(smtp_send.mask_email('not-an-address'), '***')

    def test_connect_timeout_is_logged_and_reraised(self):
        with mock.patch.object(smtp_send.smtplib, 'SMTP', side_effect=socket.timeout('timed out')), \
                self.assertLogs(self.app.logger, level='ERROR') as logs:
            with self.assertRaises(socket.timeout):
                with smtp_send.smtp_connection(SMTP_CFG, club='CTC', purpose='test'):
                    self.fail('should not connect')
        event = _events(logs)[0]
        self.assertEqual(event['event'], 'smtp.connect_failed')
        self.assertEqual(event['error_type'], 'TimeoutError')
        self.assertEqual((event['club'], event['purpose'], event['host'], event['port'], event['mode']),
                         ('CTC', 'test', 'smtp.example.org', 587, 'starttls'))
        self._assert_no_secrets(logs)

    def test_auth_failure_logs_code_but_never_password(self):
        client = _fake_smtp(login=smtplib.SMTPAuthenticationError(535, b'5.7.8 Authentication failed'))
        with mock.patch.object(smtp_send.smtplib, 'SMTP', return_value=client), \
                self.assertLogs(self.app.logger, level='DEBUG') as logs:
            with self.assertRaises(smtplib.SMTPAuthenticationError):
                with smtp_send.smtp_connection(SMTP_CFG, club='CTC', purpose='test'):
                    self.fail('should not log in')
        events = [e for e in _events(logs) if e['event'] == 'smtp.auth_failed']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['smtp_code'], 535)
        self.assertIn('Authentication failed', events[0]['smtp_response'])
        client.starttls.assert_called_once()
        client.login.assert_called_once_with('relay-user', PASSWORD)
        client.quit.assert_called_once()
        self._assert_no_secrets(logs)

    def test_ssl_mode_uses_smtp_ssl_without_starttls(self):
        client = _fake_smtp()
        cfg = dict(SMTP_CFG, useSsl=True, port=465)
        with mock.patch.object(smtp_send.smtplib, 'SMTP_SSL', return_value=client) as ssl_cls, \
                mock.patch.object(smtp_send.smtplib, 'SMTP') as plain_cls:
            with smtp_send.smtp_connection(cfg, club='CTC', purpose='test'):
                pass
        ssl_cls.assert_called_once_with('smtp.example.org', 465, timeout=smtp_send.SMTP_TIMEOUT_SECONDS)
        plain_cls.assert_not_called()
        client.starttls.assert_not_called()

    def test_successful_send_logs_message_id_and_masked_recipient(self):
        client = _fake_smtp()
        client.send_message.return_value = {}
        message = self._message()
        with self.assertLogs(self.app.logger, level='INFO') as logs:
            message_id = smtp_send.send_message(client, message, club='CTC', purpose='test')
        self.assertTrue(message_id.endswith('@club.example>'))
        self.assertEqual(message['Message-ID'], message_id)
        event = _events(logs)[0]
        self.assertEqual(event['event'], 'smtp.sent')
        self.assertEqual(event['message_id'], message_id)
        self.assertEqual(event['recipient'], 'r***@members.example')
        self._assert_no_secrets(logs)

    def test_recipients_refused_logs_send_failed_with_masked_addresses(self):
        client = _fake_smtp(send_message=smtplib.SMTPRecipientsRefused(
            {'robert@members.example': (550, b'5.1.1 User unknown')}))
        with self.assertLogs(self.app.logger, level='ERROR') as logs:
            with self.assertRaises(smtplib.SMTPRecipientsRefused):
                smtp_send.send_message(client, self._message(), club='CTC', purpose='newsletter', member_id=42)
        event = _events(logs)[0]
        self.assertEqual(event['event'], 'smtp.send_failed')
        self.assertEqual(event['member_id'], '42')
        self.assertEqual(event['refused'], [
            {'recipient': 'r***@members.example', 'smtp_code': 550, 'smtp_response': '5.1.1 User unknown'}])
        self._assert_no_secrets(logs)

    def test_scrub_addresses(self):
        self.assertEqual(
            smtp_send.scrub_addresses('550 5.1.1 <robert@members.example>: Recipient address rejected'),
            '550 5.1.1 <r***@members.example>: Recipient address rejected')
        self.assertEqual(smtp_send.scrub_addresses(None), '')

    def test_addresses_quoted_in_server_responses_are_masked(self):
        # Mail servers usually quote the full address in rejections.
        refused = smtplib.SMTPRecipientsRefused(
            {'robert@members.example': (550, b'5.1.1 <robert@members.example>: Recipient address rejected')})
        data_error = smtplib.SMTPDataError(554, b'Message to robert@members.example rejected as spam')
        for exc in (refused, data_error):
            with self.subTest(error=type(exc).__name__):
                client = _fake_smtp(send_message=exc)
                with self.assertLogs(self.app.logger, level='ERROR') as logs:
                    with self.assertRaises(type(exc)):
                        smtp_send.send_message(client, self._message(), club='CTC', purpose='newsletter')
                output = '\n'.join(r.getMessage() for r in logs.records)
                self.assertNotIn('robert@members.example', output)
                self.assertIn('r***@members.example', output)
        self._assert_no_secrets(logs)

    def test_quit_failure_after_send_is_only_logged(self):
        client = _fake_smtp(quit=smtplib.SMTPServerDisconnected('gone'))
        with mock.patch.object(smtp_send.smtplib, 'SMTP', return_value=client), \
                self.assertLogs(self.app.logger, level='WARNING') as logs:
            with smtp_send.smtp_connection(SMTP_CFG, club='CTC', purpose='test'):
                pass
        self.assertEqual(_events(logs)[0]['event'], 'smtp.quit_failed')
        client.close.assert_called_once()


class AdminSmtpTestRouteTests(unittest.TestCase):
    def setUp(self):
        deps = _MockDeps()
        deps['require_permission'] = lambda *args, **kwargs: None
        deps['get_smtp_config_for_club'] = lambda club: dict(SMTP_CFG)
        self.app = Flask(__name__)
        self.app.register_blueprint(create_admin_blueprint(deps))
        self.client = self.app.test_client()

    def test_auth_failure_response_unchanged_and_logged(self):
        client = _fake_smtp(login=smtplib.SMTPAuthenticationError(535, b'Authentication failed'))
        with mock.patch.object(smtp_send.smtplib, 'SMTP', return_value=client), \
                self.assertLogs(self.app.logger, level='ERROR') as logs:
            response = self.client.post('/admin/clubs/CTC/smtp/test', json={'toEmail': 'robert@members.example'})
        self.assertEqual(response.status_code, 502)
        self.assertTrue(response.get_json()['error'].startswith('SMTP test failed: '))
        self.assertEqual([e['event'] for e in _events(logs)], ['smtp.auth_failed'])
        self.assertNotIn(PASSWORD, '\n'.join(r.getMessage() for r in logs.records))

    def test_success_response_unchanged_and_logged(self):
        client = _fake_smtp()
        client.send_message.return_value = {}
        with mock.patch.object(smtp_send.smtplib, 'SMTP', return_value=client), \
                self.assertLogs(self.app.logger, level='INFO') as logs:
            response = self.client.post('/admin/clubs/CTC/smtp/test', json={'toEmail': 'robert@members.example'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'success': True, 'message': 'Test email sent to robert@members.example'})
        sent = [e for e in _events(logs) if e['event'] == 'smtp.sent']
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]['purpose'], 'test')


class NewsletterSendLoggingTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite://')
        metadata = MetaData()
        members = Table(
            'members', metadata,
            Column('ID', Integer, primary_key=True),
            Column('E_Mail', String),
            Column('Members_Name', String),
        )
        metadata.create_all(engine)

        class Member:
            pass

        registry().map_imperatively(Member, members)
        with engine.begin() as conn:
            conn.execute(members.insert(), [
                {'ID': 1, 'E_Mail': 'alice@members.example', 'Members_Name': 'Alice'},
                {'ID': 2, 'E_Mail': 'bob@members.example', 'Members_Name': 'Bob'},
                {'ID': 3, 'E_Mail': 'carol@members.example', 'Members_Name': 'Carol'},
            ])
        session_factory = sessionmaker(engine)

        deps = _MockDeps()
        deps['require_permission'] = lambda *args, **kwargs: None
        deps['get_valid_club_short_names'] = lambda: ['CTC']
        deps['get_smtp_config_for_club'] = lambda club: dict(SMTP_CFG)
        deps['log_database_target'] = lambda club: None
        deps['get_read_db_for_club'] = lambda club: {
            'session': session_factory(), 'members_table': members, 'Member': Member,
            'newsletter_templates_table': None,
        }
        deps['get_identifier_column'] = lambda table: table.c.ID
        deps['get_column'] = lambda name, table: table.c.get(name)
        deps['member_to_dict'] = lambda member, table: {c.name: getattr(member, c.name) for c in table.columns}
        deps['render_newsletter_template'] = lambda text, context: text
        deps['NEWSLETTER_TEMPLATES'] = {'t1': {'id': 't1', 'subject': 'News', 'body': 'Body text'}}
        deps['NEWSLETTER_TEMPLATE_TAGS'] = []
        self.app = Flask(__name__)
        self.app.register_blueprint(create_newsletter_blueprint(deps))
        self.client = self.app.test_client()

    def _send(self):
        return self.client.post('/newsletter/send', json={'club': 'CTC', 'templateId': 't1', 'scope': 'all_club'})

    def test_partial_failure_logs_each_failure_and_one_summary(self):
        client = _fake_smtp()

        def send(message):
            if message['To'] == 'bob@members.example':
                raise smtplib.SMTPRecipientsRefused({'bob@members.example': (550, b'User unknown')})
            return {}

        client.send_message.side_effect = send
        with mock.patch.object(smtp_send.smtplib, 'SMTP', return_value=client), \
                self.assertLogs(self.app.logger, level='INFO') as logs:
            response = self._send()

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual((body['sentCount'], body['failedCount']), (2, 1))
        self.assertEqual(body['failedDeliveries'][0]['email'], 'bob@members.example')

        events = _events(logs)
        names = [e['event'] for e in events]
        self.assertEqual(names.count('smtp.send_failed'), 1)
        self.assertEqual(names.count('smtp.batch_summary'), 1)
        self.assertNotIn('smtp.sent', names)  # per-recipient success is DEBUG only
        summary = next(e for e in events if e['event'] == 'smtp.batch_summary')
        self.assertEqual((summary['total'], summary['sent'], summary['failed']), (3, 2, 1))
        failed = next(e for e in events if e['event'] == 'smtp.send_failed')
        self.assertEqual(failed['member_id'], '2')
        output = '\n'.join(r.getMessage() for r in logs.records)
        for secret in (PASSWORD, 'bob@members.example', 'alice@members.example', 'Body text'):
            self.assertNotIn(secret, output)

    def test_prepare_recipients_with_real_columns(self):
        # Regression: `get_column(a) or get_column(b)` raised TypeError (500)
        # whenever the first column existed, as E_Mail does on real tables.
        response = self.client.post('/newsletter/prepare_recipients', json={'club': 'CTC', 'memberIds': [1, 3]})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['emailableCount'], 2)
        self.assertEqual(sorted(r['E_Mail'] for r in body['recipients']),
                         ['alice@members.example', 'carol@members.example'])

    def test_login_failure_response_unchanged_and_summary_marks_abort(self):
        client = _fake_smtp(login=smtplib.SMTPAuthenticationError(535, b'Authentication failed'))
        with mock.patch.object(smtp_send.smtplib, 'SMTP', return_value=client), \
                self.assertLogs(self.app.logger, level='INFO') as logs:
            response = self._send()
        self.assertEqual(response.status_code, 502)
        self.assertTrue(response.get_json()['error'].startswith('Failed to connect or authenticate with SMTP server: '))
        events = _events(logs)
        self.assertEqual([e['event'] for e in events], ['smtp.auth_failed', 'smtp.batch_summary'])
        self.assertTrue(events[1]['aborted'])
        self.assertEqual((events[1]['sent'], events[1]['failed']), (0, 3))
        client.send_message.assert_not_called()


if __name__ == '__main__':
    unittest.main()
