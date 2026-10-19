import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

builder = load('version_builder', 'build.py')
upgrade = load('version_upgrader', 'prepare_upgrade.py')


class VersionTransitionTests(unittest.TestCase):
    def test_fresh_old_version_then_new_version(self):
        source = builder.make_compose('erpnext.test', 18083, 'not-a-real-password', 'fake-db-password', 'v16.51.0')
        for service in source['services'].values():
            if service.get('image', '').startswith('frappe/erpnext:'):
                self.assertEqual(service['image'], 'frappe/erpnext:v16.51.0')
        stages = upgrade.numbered_stages(upgrade.prepare(source, 'frappe/erpnext:v16.51.1'))
        self.assertEqual(len(stages), 5)
        self.assertEqual(len({name[:2] for name in stages}), 5)
        self.assertEqual(stages['01-backup.yaml']['services']['upgrade-job']['image'], 'frappe/erpnext:v16.51.0')
        self.assertEqual(stages['04-migrate.yaml']['services']['upgrade-job']['image'], 'frappe/erpnext:v16.51.1')
        resume = stages['05-resume.yaml']
        for service in resume['services'].values():
            if service.get('image', '').startswith('frappe/erpnext:'):
                self.assertEqual(service['image'], 'frappe/erpnext:v16.51.1')
        self.assertEqual(source['services']['db'], resume['services']['db'])
        self.assertEqual(source['services']['frontend']['ports'], resume['services']['frontend']['ports'])
        self.assertEqual(source['volumes'], resume['volumes'])
        self.assertEqual(stages['03-verify-startup-blocked.yaml'], stages['05-resume.yaml'])

    def test_refuses_floating_or_different_major_install(self):
        for tag in ('latest', 'version-16', 'v15.99.0', 'v17.0.0', 'v16.51.0;echo bad'):
            with self.assertRaises(ValueError):
                builder.make_compose('erpnext.test', 18083, 'not-a-real-password', 'fake', tag)


if __name__ == '__main__':
    unittest.main()
