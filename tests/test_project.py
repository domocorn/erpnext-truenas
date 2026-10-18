import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import os
import yaml

ROOT = Path(__file__).resolve().parents[1]
def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
build = module('builder', 'build.py')
init = module('initializer', 'initialize.py')

class DeploymentTests(unittest.TestCase):
    def test_isolation_and_credentials(self):
        d = build.make_compose('erpnext.test', 18081, 'test$password123', 'db$secret')
        self.assertEqual(yaml.safe_load(yaml.safe_dump(d)), d)
        self.assertNotIn('name', d)
        self.assertTrue(all(v == {} for v in d['volumes'].values()))
        published = [n for n, s in d['services'].items() if s.get('ports')]
        self.assertEqual(published, ['frontend'])
        self.assertEqual(d['services']['initializer']['environment']['ADMIN_PASSWORD'], 'test$$password123')
        for name in ['backend', 'frontend', 'queue-long', 'queue-short', 'websocket', 'scheduler']:
            self.assertEqual(d['services'][name]['depends_on']['initializer']['condition'], 'service_completed_successfully')

    def test_refuse_unsafe_site_name(self):
        with self.assertRaises(ValueError):
            build.make_compose('../live', 18081, 'password123456', 'db')

class InitializationTests(unittest.TestCase):
    def run_in_directory(self, setup):
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            try:
                os.chdir(tmp)
                Path('sites').mkdir()
                setup()
            finally:
                os.chdir(previous)

    @patch.dict(os.environ, {'SITE_NAME': 'erpnext.test', 'ADMIN_PASSWORD': 'test-password', 'DB_ROOT_PASSWORD': 'db-password'})
    def test_interrupted_install_never_retries_blindly(self):
        def check():
            Path('sites/.nas-installing-erpnext.test').touch()
            with patch.object(init.subprocess, 'run') as run:
                with self.assertRaises(SystemExit):
                    init.main()
                run.assert_not_called()
        self.run_in_directory(check)

    @patch.dict(os.environ, {'SITE_NAME': 'erpnext.test'})
    def test_unmanaged_site_never_overwritten(self):
        def check():
            Path('sites/erpnext.test').mkdir()
            with patch.object(init.subprocess, 'run') as run:
                with self.assertRaises(SystemExit):
                    init.main()
                run.assert_not_called()
        self.run_in_directory(check)

    @patch.dict(os.environ, {'SITE_NAME': 'erpnext.test'})
    def test_verified_site_does_not_reset_password(self):
        def check():
            p = Path('sites/erpnext.test')
            p.mkdir()
            (p / '.nas-initialized').touch()
            with patch.object(init.subprocess, 'check_output', return_value='["frappe", "erpnext"]'), patch.object(init.subprocess, 'run') as run:
                init.main()
                run.assert_not_called()
        self.run_in_directory(check)

if __name__ == '__main__':
    unittest.main()
