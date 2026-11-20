"""CORE-35 (#62): explicit `member` base role; grant on a recorded role, deny on absence."""
import unittest
from unittest import mock

from flask import Flask
from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, create_engine, text
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

import auth.principal as principal
from db.postgres_backend import sync_member_roles
from routes.member_routes import create_member_blueprint
from security.permissions import MEMBER_ROLE_CODE, expand_role_codes, has_permission, list_permissions

ROLE_IDS = {'member': 1, 'committee': 2, 'club_admin': 3, 'club_manager': 4, 'app_admin': 5, 'app_owner': 6}
CTC, GAAFFS = 10, 20


class _MockDeps(dict):
    def __missing__(self, key):
        value = mock.MagicMock(name=key)
        self[key] = value
        return value


# Minimal SQLite versions of the tables involved (the real ones use JSONB etc.).
META = MetaData()
CLUBS = Table('clubs', META, Column('id', Integer, primary_key=True), Column('short_name', String),
              Column('full_name', String), Column('is_active', Boolean))
MEMBERS = Table('members', META, Column('id', Integer, primary_key=True), Column('club_id', Integer),
                Column('members_name', String), Column('number', String), Column('member_type', String),
                Column('paid_up_2026', String), Column('resigned', String))
APP_USERS = Table('app_users', META, Column('id', Integer, primary_key=True), Column('username', String),
                  Column('email', String), Column('display_name', String), Column('password_hash', String),
                  Column('is_active', Boolean))
LINKS = Table('member_user_links', META, Column('id', Integer, primary_key=True), Column('user_id', Integer),
              Column('member_id', Integer), Column('club_id', Integer), Column('is_primary', Boolean))
ROLES = Table('roles', META, Column('id', Integer, primary_key=True), Column('code', String), Column('name', String),
              Column('scope_type', String), Column('is_system', Boolean))
ASSIGNMENTS = Table('member_role_assignments', META, Column('id', Integer, primary_key=True),
                    Column('user_id', Integer), Column('role_id', Integer), Column('club_id', Integer),
                    Column('source', String, nullable=False, server_default='admin'),
                    Column('granted_at', DateTime), Column('revoked_at', DateTime))


def _make_db():
    """SQLite stand-in for the RBAC/account tables."""
    engine = create_engine('sqlite://')
    META.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE UNIQUE INDEX uq_mra_user_role_club_active ON member_role_assignments (user_id, role_id, club_id) "
            "WHERE club_id IS NOT NULL AND revoked_at IS NULL"))
        for code, role_id in ROLE_IDS.items():
            scope = 'global' if code in ('app_admin', 'app_owner') else 'club'
            conn.execute(text("INSERT INTO roles (id, code, name, scope_type, is_system) VALUES (:i, :c, :c, :s, 1)"),
                         {'i': role_id, 'c': code, 's': scope})
        conn.execute(text("INSERT INTO clubs (id, short_name, full_name, is_active) VALUES (10, 'CTC', 'CTC', 1), (20, 'GAAFFS', 'GAAFFS', 1)"))
    return engine


def _add_member(conn, member_id, user_id, club_id, resigned='', member_type='Ordinary', username=None, password=''):
    conn.execute(text(
        "INSERT INTO members (id, club_id, members_name, number, member_type, paid_up_2026, resigned) "
        "VALUES (:id, :club, :name, :id, :type, '', :resigned)"),
        {'id': member_id, 'club': club_id, 'name': f'Member {member_id}', 'type': member_type, 'resigned': resigned})
    conn.execute(text(
        "INSERT OR IGNORE INTO app_users (id, username, email, display_name, password_hash, is_active) "
        "VALUES (:u, :name, '', :name, :pw, 1)"),
        {'u': user_id, 'name': username or f'user{user_id}', 'pw': password})
    conn.execute(text("INSERT INTO member_user_links (id, user_id, member_id, club_id, is_primary) VALUES (:id, :u, :m, :c, 1)"),
                 {'id': member_id, 'u': user_id, 'm': member_id, 'c': club_id})


def _grant(conn, assignment_id, user_id, role, club_id, source='admin', revoked=False):
    conn.execute(text(
        "INSERT INTO member_role_assignments (id, user_id, role_id, club_id, source, granted_at, revoked_at) "
        "VALUES (:id, :u, :r, :c, :s, CURRENT_TIMESTAMP, :rev)"),
        {'id': assignment_id, 'u': user_id, 'r': ROLE_IDS[role], 'c': club_id, 's': source,
         'rev': '2026-11-20 00:00:00' if revoked else None})


def _active_member_rows(conn, user_id, club_id):
    return conn.execute(text(
        "SELECT source FROM member_role_assignments WHERE user_id = :u AND club_id = :c "
        "AND role_id = :r AND revoked_at IS NULL"), {'u': user_id, 'c': club_id, 'r': ROLE_IDS['member']}).scalars().all()


class PermissionModelTests(unittest.TestCase):
    def test_no_roles_means_no_permissions(self):
        self.assertEqual(expand_role_codes(set()), set())
        self.assertEqual(list_permissions(set()), [])
        self.assertFalse(has_permission(set(), 'member.self.read'))

    def test_member_is_the_base_role(self):
        self.assertEqual(MEMBER_ROLE_CODE, 'member')
        self.assertTrue(has_permission({'member'}, 'member.self.read'))
        self.assertTrue(has_permission({'member'}, 'member.self.update'))
        self.assertFalse(has_permission({'member'}, 'member.club.list'))
        self.assertFalse(has_permission({'user'}, 'member.self.read'))  # old code grants nothing

    def test_elevated_roles_are_layered_on_member(self):
        for role in ('committee', 'club_admin', 'club_manager', 'app_admin', 'app_owner'):
            self.assertIn('member', expand_role_codes({role}), role)
        self.assertTrue(has_permission({'committee'}, 'member.club.list'))


class SyncMemberRolesTests(unittest.TestCase):
    def setUp(self):
        self.engine = _make_db()

    def _sync(self, club_id=None):
        with self.engine.begin() as conn:
            return sync_member_roles(conn, club_id=club_id)

    def test_grants_active_and_paused_members_not_resigned(self):
        with self.engine.begin() as conn:
            _add_member(conn, 1, 101, CTC)                            # active
            _add_member(conn, 2, 102, CTC, member_type='Paused')       # Holding List keeps member
            _add_member(conn, 3, 103, CTC, resigned='Y')               # resigned by flag
            _add_member(conn, 4, 104, CTC, member_type='Resigned')     # resigned by type
        self.assertEqual(self._sync(), {'granted': 2, 'revoked': 0})
        with self.engine.connect() as conn:
            self.assertEqual(_active_member_rows(conn, 101, CTC), ['auto'])
            self.assertEqual(_active_member_rows(conn, 102, CTC), ['auto'])
            self.assertEqual(_active_member_rows(conn, 103, CTC), [])
            self.assertEqual(_active_member_rows(conn, 104, CTC), [])

    def test_idempotent(self):
        with self.engine.begin() as conn:
            _add_member(conn, 1, 101, CTC)
        self._sync()
        self.assertEqual(self._sync(), {'granted': 0, 'revoked': 0})

    def test_resignation_and_deletion_revoke_auto_role(self):
        with self.engine.begin() as conn:
            _add_member(conn, 1, 101, CTC)
            _add_member(conn, 2, 102, CTC)
        self._sync()
        with self.engine.begin() as conn:
            conn.execute(text("UPDATE members SET resigned = 'Y' WHERE id = 1"))
            conn.execute(text("DELETE FROM member_user_links WHERE member_id = 2"))  # cascades on member delete
        self.assertEqual(self._sync(), {'granted': 0, 'revoked': 2})
        with self.engine.connect() as conn:
            self.assertEqual(_active_member_rows(conn, 101, CTC), [])
            self.assertEqual(_active_member_rows(conn, 102, CTC), [])

    def test_admin_revoke_is_not_regranted(self):
        with self.engine.begin() as conn:
            _add_member(conn, 1, 101, CTC)
            _grant(conn, 1, 101, 'member', CTC, source='admin', revoked=True)
        self.assertEqual(self._sync(), {'granted': 0, 'revoked': 0})

    def test_admin_grant_survives_resignation(self):
        with self.engine.begin() as conn:
            _add_member(conn, 1, 101, CTC, resigned='Y')
            _grant(conn, 1, 101, 'member', CTC, source='admin')
        self.assertEqual(self._sync(), {'granted': 0, 'revoked': 0})
        with self.engine.connect() as conn:
            self.assertEqual(_active_member_rows(conn, 101, CTC), ['admin'])

    def test_club_filter_only_touches_that_club(self):
        with self.engine.begin() as conn:
            _add_member(conn, 1, 101, CTC)
            _add_member(conn, 2, 102, GAAFFS)
        self.assertEqual(self._sync(club_id=CTC), {'granted': 1, 'revoked': 0})
        with self.engine.connect() as conn:
            self.assertEqual(_active_member_rows(conn, 102, GAAFFS), [])

    def test_no_member_role_row_is_a_no_op(self):
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM roles WHERE code = 'member'"))
            _add_member(conn, 1, 101, CTC)
        self.assertEqual(self._sync(), {'granted': 0, 'revoked': 0})


class LoadMemberRolesTests(unittest.TestCase):
    def setUp(self):
        self.engine = _make_db()
        backend = {
            'session_factory': sessionmaker(self.engine),
            'roles_table': ROLES,
            'member_role_assignments_table': ASSIGNMENTS,
            'clubs_table': CLUBS,
            'member_user_links_table': LINKS,
        }
        for patcher in (mock.patch.object(principal, 'is_postgres_reads_enabled', return_value=True),
                        mock.patch.object(principal, 'get_postgres_backend', return_value=backend)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def _roles(self, user_id, club='CTC'):
        return principal.load_member_roles(None, club, user_id=user_id)

    def test_member_only(self):
        with self.engine.begin() as conn:
            _grant(conn, 1, 101, 'member', CTC)
        roles = self._roles(101)
        self.assertEqual(roles['club_roles'], ['member'])
        self.assertIn('member.self.update', roles['permissions'])
        self.assertTrue(principal.has_club_membership(roles))

    def test_no_assignment_means_nothing(self):
        roles = self._roles(101)
        self.assertEqual((roles['effective_roles'], roles['permissions']), ([], []))
        self.assertFalse(principal.has_club_membership(roles))

    def test_elevated_club_role_needs_member(self):
        with self.engine.begin() as conn:
            _grant(conn, 1, 101, 'committee', CTC)               # e.g. resigned committee member
            _grant(conn, 2, 102, 'committee', CTC)
            _grant(conn, 3, 102, 'member', CTC)
        without_member = self._roles(101)
        self.assertEqual(without_member['club_roles'], [])
        self.assertNotIn('member.club.list', without_member['permissions'])
        with_member = self._roles(102)
        self.assertEqual(with_member['club_roles'], ['committee', 'member'])
        self.assertIn('member.club.list', with_member['permissions'])

    def test_roles_are_per_club(self):
        with self.engine.begin() as conn:
            _grant(conn, 1, 101, 'member', CTC)
            _grant(conn, 2, 101, 'club_admin', CTC)
        self.assertFalse(principal.has_club_membership(self._roles(101, club='GAAFFS')))

    def test_global_admin_has_access_without_club_roles(self):
        with self.engine.begin() as conn:
            _grant(conn, 1, 101, 'app_admin', None)
        roles = self._roles(101, club='GAAFFS')
        self.assertTrue(principal.has_club_membership(roles))
        self.assertIn('member.club.update', roles['permissions'])

    def test_no_linked_account_means_nothing(self):
        roles = principal.load_member_roles(999, 'CTC', user_id=None)
        self.assertEqual(roles['effective_roles'], [])

    def test_fallback_mode_implies_member(self):
        with mock.patch.object(principal, 'is_postgres_reads_enabled', return_value=False):
            roles = principal.load_member_roles(1, 'CTC')
        self.assertEqual(roles['club_roles'], ['member'])
        self.assertTrue(principal.has_club_membership(roles))


class RequireAuthenticatedTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def _check(self, principal_value):
        with self.app.test_request_context(), \
                mock.patch.object(principal, 'get_current_principal', return_value=principal_value):
            result = principal.require_authenticated('CTC')
        return None if result is None else result[1]

    def test_refuses_member_session_without_member_role(self):
        self.assertEqual(self._check({'user_type': 'member', 'global_roles': [], 'club_roles': []}), 403)
        self.assertEqual(self._check({'user_type': 'member', 'global_roles': [], 'club_roles': ['committee']}), 403)

    def test_allows_member_and_global_admin(self):
        self.assertIsNone(self._check({'user_type': 'member', 'global_roles': [], 'club_roles': ['member']}))
        self.assertIsNone(self._check({'user_type': 'member', 'global_roles': ['app_owner'], 'club_roles': []}))

    def test_no_session(self):
        self.assertEqual(self._check(None), 401)


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.engine = _make_db()
        with self.engine.begin() as conn:
            _add_member(conn, 1, 101, CTC, username='alice', password=generate_password_hash('right-pass'))
        self.club_roles = ['member']
        deps = _MockDeps()
        deps['get_valid_club_short_names'] = lambda: ['CTC']
        deps['is_postgres_reads_enabled'] = lambda: True
        deps['get_postgres_backend'] = lambda: {
            'session_factory': sessionmaker(self.engine),
            'app_users_table': APP_USERS,
            'member_user_links_table': LINKS,
            'clubs_table': CLUBS,
        }
        deps['load_member_roles'] = lambda member_id, club, user_id=None: {
            'global_roles': [], 'club_roles': list(self.club_roles),
            'effective_roles': list(self.club_roles), 'permissions': list_permissions(set(self.club_roles)),
        }
        deps['issue_member_token_pair'] = lambda *args, **kwargs: {'token': 't', 'refreshToken': 'r'}
        app = Flask(__name__)
        app.register_blueprint(create_member_blueprint(deps))
        self.client = app.test_client()
        self.deps = deps

    def _login(self, username, password='right-pass'):
        return self.client.post('/login', json={'username': username, 'password': password, 'club': 'CTC'})

    def test_active_member_signs_in(self):
        response = self._login('alice')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['roles'], ['member'])

    def test_inactive_membership_refused_before_tokens(self):
        self.club_roles = []
        issue = mock.MagicMock(return_value={'token': 't', 'refreshToken': 'r'})
        self.deps['issue_member_token_pair'] = issue
        response = self._login('alice')
        self.assertEqual(response.status_code, 403)
        self.assertIn('not active', response.get_json()['error'])

    def test_sign_in_by_name_is_retired(self):
        # 'Member 1' is the members_name; it isn't an app_users username.
        response = self._login('Member 1')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()['error'], 'Invalid credentials')
        self.deps['get_read_db_for_club'].assert_not_called()


if __name__ == '__main__':
    unittest.main()
