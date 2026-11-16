import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


BUILD_SCRIPT = Path(__file__).resolve().parents[2] / 'hlas_build.sh'


class CleanOnlyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.log = self.directory / 'docker.log'
        docker = self.directory / 'docker'
        docker.write_text(
            '#!/usr/bin/python3\nimport json, os, sys\n'
            "args = sys.argv[1:]\n"
            "with open(os.environ['MOCK_DOCKER_LOG'], 'a') as log:\n"
            "    log.write(json.dumps(args) + '\\n')\n"
            "if args == ['system', 'prune', '-f'] and os.environ.get('FAIL_PRUNE'):\n"
            "    sys.exit(1)\n"
            "if 'build' in args and os.environ.get('FAIL_BUILD'):\n"
            "    sys.exit(1)\n"
        )
        docker.chmod(0o755)
        make = self.directory / 'make'
        make.write_text('#!/bin/sh\nexit 1\n')
        make.chmod(0o755)

    def run_script(self, *args, isolated_path=False, **extra_env):
        env = os.environ.copy()
        env.update({
            'PATH': str(self.directory) if isolated_path else f'{self.directory}:/usr/bin:/bin',
            'MOCK_DOCKER_LOG': str(self.log),
            **extra_env,
        })
        result = subprocess.run(
            ['/bin/bash', str(BUILD_SCRIPT), *args],
            env=env, capture_output=True, text=True, timeout=30,
        )
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        return result, calls

    def test_clean_only_skips_deployment_and_python_requirements(self):
        result, calls = self.run_script(
            '--remote', '--directory', str(self.directory / 'missing'),
            '--clean-only', isolated_path=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls, [['system', 'prune', '-f']])
        self.assertIn('across the Docker host', result.stdout)
        self.assertNotIn('Build complete', result.stdout)

    def test_clean_only_reports_prune_failure(self):
        result, calls = self.run_script('--clean-only', FAIL_PRUNE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [['system', 'prune', '-f']])
        self.assertIn('Docker cleanup failed', result.stderr)
        self.assertNotIn('clean complete', result.stdout)

    def test_cleanup_flag_order_never_falls_through_to_build(self):
        result, calls = self.run_script('--clean-only', '--noclean')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--clean-only cannot run', result.stderr)
        self.assertEqual(calls, [])
        result, calls = self.run_script('--noclean', '--clean-only')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls, [['system', 'prune', '-f']])

    def test_post_build_clean_runs_only_on_success(self):
        (self.directory / '.env.dev').write_text(
            'WORDPRESS_DB_HOST=test\nWORDPRESS_DB_NAME=test\n'
            'WORDPRESS_DB_ROOT_PASSWORD=test\nWORDPRESS_DB_USER=test\n'
            'WORDPRESS_DB_PASSWORD=test\n'
        )
        (self.directory / 'caddyfile').write_text('test')
        (self.directory / 'clubs.json').write_text('{}')
        args = (
            '--target', 'development', '--directory', str(self.directory), '--local', '--nohealth',
            '--caddyfile', 'caddyfile', '--clubs-config', 'clubs.json', '--clean',
        )
        result, calls = self.run_script(*args, FAIL_BUILD='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(['system', 'prune', '-f'], calls)
        self.log.unlink()
        result, calls = self.run_script(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(any('build' in call for call in calls))
        self.assertEqual(calls[-1], ['system', 'prune', '-f'])


if __name__ == '__main__':
    unittest.main()
