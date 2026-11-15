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
if args == ['system', 'prune', '-f'] and os.environ.get('MOCK_PRUNE_FAIL') == 'true':
    print('mock prune failure', file=sys.stderr)
    sys.exit(1)
elif args[0] == 'inspect':
    print(os.environ.get('MOCK_PG_HEALTH', 'healthy'))
elif 'config' in args:
    print(json.dumps({'services': {'backend': {'environment': {
        'HLAS_SYNC_FILES_ON_STARTUP': os.environ.get('MOCK_SYNC', 'false')
    }}}}))
elif 'ps' in args and '-q' in args:
    print('postgres-test-id')
elif 'ps' in args and '--services' in args:
    print('\\n'.join(['postgres', 'backend', 'frontend', 'wordpress-db',
                     'wordpress', 'wordpress-web', 'caddy']))
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
            ('git', '#!/usr/bin/python3\nimport json, os, sys\n'
             'with open(os.environ["MOCK_GIT_LOG"], "a") as log:\n'
             '    log.write(json.dumps(sys.argv[1:]) + "\\n")\n'),
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
        self.log = self.directory / 'docker.log'
        self.git_log = self.directory / 'git.log'

    def run_build(self, *args, **extra_env):
        env = os.environ.copy()
        env.update({
            'PATH': f'{self.directory}:/usr/bin:/bin',
            'MOCK_DOCKER_LOG': str(self.log),
            'MOCK_GIT_LOG': str(self.git_log),
            **extra_env,
        })
        result = subprocess.run(
            ['/bin/bash', str(BUILD_SCRIPT), '--target', 'ctc-production',
             '--directory', str(self.directory), '--local', '--quick',
             '--caddyfile', 'caddyfile', '--clubs-config', 'clubs.json', *args],
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

    def test_clean_only_prunes_without_deployment_prerequisites(self):
        (self.directory / '.env.ctc').unlink()
        result, calls = self.run_build(
            '--remote', '--directory', str(self.directory / 'missing'), '--clean-only',
            PATH=str(self.directory),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls, [['system', 'prune', '-f']])
        self.assertFalse(self.git_log.exists())
        self.assertIn('across the Docker host', result.stdout)
        self.assertNotIn('Build complete', result.stdout)

    def test_clean_only_reports_prune_failure(self):
        result, calls = self.run_build('--clean-only', MOCK_PRUNE_FAIL='true')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [['system', 'prune', '-f']])
        self.assertIn('Docker cleanup failed', result.stderr)
        self.assertNotIn('clean complete', result.stdout)

    def test_clean_only_respects_cleanup_flag_order_without_building(self):
        result, calls = self.run_build('--clean-only', '--noclean')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--clean-only cannot run', result.stderr)
        self.assertEqual(calls, [])
        self.assertFalse(self.git_log.exists())

        result, calls = self.run_build('--noclean', '--clean-only')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls, [['system', 'prune', '-f']])

    def test_post_build_clean_still_runs_after_success(self):
        result, calls = self.run_build('--clean')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls[-1], ['system', 'prune', '-f'])
        self.assertTrue(any('build' in call for call in calls))

    def test_post_build_clean_does_not_run_on_failure(self):
        result, calls = self.run_build('--app-only', '--clean', MOCK_SYNC='true')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(['system', 'prune', '-f'], calls)


if __name__ == '__main__':
    unittest.main()
