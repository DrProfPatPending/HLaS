import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


BUILD_SCRIPT = Path(__file__).resolve().parents[2] / 'hlas_build.sh'

DOCKER_STUB = """#!/usr/bin/python3
import json
import os
import sys

args = sys.argv[1:]
with open(os.environ['MOCK_DOCKER_LOG'], 'a') as log:
    log.write(json.dumps(args) + '\\n')
if args[0] == 'inspect':
    print(os.environ.get('MOCK_PG_HEALTH', 'healthy'))
elif 'config' in args:
    print(json.dumps({'services': {'backend': {'environment': {
        'HLAS_SYNC_FILES_ON_STARTUP': os.environ.get('MOCK_SYNC', 'false')
    }}}}))
elif 'ps' in args and '-q' in args:
    print('postgres-test-id')
elif 'ps' in args and '--services' in args:
    services = ['postgres', 'backend', 'frontend', 'caddy']
    if 'docker-compose.ctc-dev.yml' not in args:
        services += ['wordpress-db', 'wordpress', 'wordpress-web']
    print('\\n'.join(services))
"""


class BuildScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for name, content in (
            ('docker', DOCKER_STUB),
            ('make', '#!/bin/sh\nexit 1\n'),
            ('curl', '#!/bin/sh\nprintf 200\n'),
        ):
            executable = self.directory / name
            executable.write_text(content)
            executable.chmod(0o755)
        (self.directory / '.env.ctc').write_text(
            'WORDPRESS_DB_HOST=test\nWORDPRESS_DB_NAME=test\n'
            'WORDPRESS_DB_ROOT_PASSWORD=test\nWORDPRESS_DB_USER=test\n'
            'WORDPRESS_DB_PASSWORD=test\n'
        )
        (self.directory / 'caddyfile').write_text('test')
        (self.directory / 'clubs.json').write_text('{}')
        deploy = self.directory / 'deploy'
        (deploy / 'caddy').mkdir(parents=True)
        (deploy / 'caddy' / 'Caddyfile.ctc-dev').write_text('test')
        (deploy / 'clubs.config.ctc-dev.json').write_text('{}')
        (deploy / '.ctc-dev-postgres-password').write_text('development-test-only')
        self.log = self.directory / 'docker.log'
        self.git_log = self.directory / 'git.log'
        git = self.directory / 'git'
        git.write_text(
            '#!/usr/bin/python3\nimport json, os, sys\n'
            "with open(os.environ['MOCK_GIT_LOG'], 'a') as log:\n"
            "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        )
        git.chmod(0o755)

    def run_build(self, *args, target='ctc-production', **extra_env):
        env = os.environ.copy()
        env.update({
            'PATH': f'{self.directory}:/usr/bin:/bin',
            'MOCK_DOCKER_LOG': str(self.log),
            'MOCK_GIT_LOG': str(self.git_log),
            **extra_env,
        })
        options = [] if target == 'ctc-dev' else [
            '--caddyfile', 'caddyfile', '--clubs-config', 'clubs.json',
        ]
        result = subprocess.run(
            ['/bin/bash', str(BUILD_SCRIPT), '--target', target,
             '--directory', str(self.directory), '--local', '--quick', *options, *args],
            env=env, capture_output=True, text=True, timeout=30,
        )
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        return result, calls

    def test_app_only_starts_only_app_without_dependencies(self):
        result, calls = self.run_build('--app-only')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        up_calls = [call for call in calls if 'up' in call]
        self.assertEqual([call[-1] for call in up_calls], ['backend', 'frontend'])
        for call in up_calls:
            self.assertIn('--no-deps', call)
            self.assertIn('--wait', call)
        self.assertTrue(any('build' in call and call[-2:] == ['backend', 'frontend'] for call in calls))
        self.assertTrue(any('exec' in call and 'wordpress-web' in call for call in calls))

    def test_app_only_rejects_enabled_ctc_startup_sync_before_building(self):
        result, calls = self.run_build('--app-only', MOCK_SYNC='true')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('HLAS_SYNC_FILES_ON_STARTUP=false', result.stderr)
        self.assertFalse(any('build' in call or 'up' in call for call in calls))

    def test_app_only_rejects_unhealthy_postgres_before_building(self):
        result, calls = self.run_build('--app-only', MOCK_PG_HEALTH='unhealthy')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('healthy PostgreSQL', result.stderr)
        self.assertFalse(any('build' in call or 'up' in call for call in calls))

    def test_default_mode_still_starts_all_services(self):
        result, calls = self.run_build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        up_calls = [call for call in calls if 'up' in call]
        self.assertEqual([call[-1] for call in up_calls],
                         ['wordpress-db', 'frontend', 'wordpress-web', 'caddy'])
        self.assertFalse(any('--no-deps' in call for call in up_calls))

    def test_ctc_dev_app_only_uses_isolated_stack_without_production_env(self):
        (self.directory / '.env.ctc').unlink()
        result, calls = self.run_build('--app-only', target='ctc-dev')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        compose_calls = [call for call in calls if call[0] == 'compose']
        for call in compose_calls:
            self.assertEqual(call[1:7], [
                '--env-file', '/dev/null', '--project-name', 'ctc-dev',
                '-f', 'docker-compose.ctc-dev.yml',
            ])
            self.assertFalse(any('wordpress' in argument for argument in call))
        up_calls = [call for call in calls if 'up' in call]
        self.assertEqual([call[-1] for call in up_calls], ['backend', 'frontend'])
        self.assertTrue(all('--no-deps' in call and '--wait' in call for call in up_calls))
        self.assertTrue(any('exec' in call and 'backend' in call and 'python' in call for call in calls))
        self.assertFalse(self.git_log.exists())

    def test_ctc_dev_remote_mode_selects_correct_branch(self):
        result, _ = self.run_build('--app-only', '--remote', target='ctc-dev')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        git_calls = [json.loads(line) for line in self.git_log.read_text().splitlines()]
        self.assertEqual(git_calls, [
            ['checkout', 'ctc-dev'], ['fetch', 'origin'],
            ['reset', '--hard', 'origin/ctc-dev'],
        ])

    def test_ctc_dev_full_mode_does_not_start_wordpress(self):
        result, calls = self.run_build(target='ctc-dev')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual([call[-1] for call in calls if 'up' in call],
                         ['postgres', 'frontend', 'caddy'])
        self.assertFalse(any('wordpress' in argument for call in calls for argument in call))

    def test_ctc_dev_rejects_missing_secret(self):
        (self.directory / 'deploy' / '.ctc-dev-postgres-password').unlink()
        result, calls = self.run_build('--app-only', target='ctc-dev')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('existing non-empty', result.stderr)
        self.assertFalse(any('build' in call or 'up' in call for call in calls))

    def test_ctc_dev_rejects_unsafe_app_only_prerequisites(self):
        for settings, error in [
            ({'MOCK_SYNC': 'true'}, 'HLAS_SYNC_FILES_ON_STARTUP=false'),
            ({'MOCK_PG_HEALTH': 'unhealthy'}, 'healthy PostgreSQL'),
        ]:
            with self.subTest(settings=settings):
                result, calls = self.run_build('--app-only', target='ctc-dev', **settings)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
                self.assertFalse(any('build' in call or 'up' in call for call in calls))

    def test_ctc_dev_rejects_ignored_configuration_overrides(self):
        for flag in ('--env-file', '--caddyfile', '--clubs-config'):
            with self.subTest(flag=flag):
                result, calls = self.run_build('--app-only', flag, 'other', target='ctc-dev')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('fixed isolated configuration', result.stderr)
                self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
