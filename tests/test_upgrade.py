import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

builder = load('upgrade_builder', 'build.py')
upgrade = load('upgrade_generator', 'prepare_upgrade.py')
init = load('guarded_initializer', 'initialize.py')
OP = 'a' * 32
IMAGE = 'frappe/erpnext:v16.51.1'


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.original = builder.make_compose('erpnext.test', 18082, 'example-password', 'db$$password')

    def test_preserves_secrets_storage_and_port(self):
        docs = upgrade.prepare(self.original, IMAGE, rehearsal=True, operation=OP)
        resume = docs['03-resume.yaml']
        self.assertEqual(resume['volumes'], self.original['volumes'])
        self.assertEqual(resume['services']['db'], self.original['services']['db'])
        self.assertEqual(resume['services']['frontend'], self.original['services']['frontend'])
        self.assertEqual(resume['services']['initializer']['environment']['DB_ROOT_PASSWORD'], 'db$$$$password')
        for name in ('01-backup.yaml', '02-migrate.yaml', '02-test-failure.yaml'):
            self.assertEqual(set(docs[name]['services']), {'db', 'redis-cache', 'redis-queue', 'upgrade-job'})
            self.assertFalse(any(s.get('ports') for s in docs[name]['services'].values()))

    def test_versions(self):
        for image in ('frappe/erpnext:latest', 'frappe/erpnext:v15.99.0', 'frappe/erpnext:v17.0.0', 'frappe/erpnext:v16.51.0', IMAGE):
            with self.assertRaises(ValueError):
                upgrade.prepare(self.original, image)
        docs = upgrade.prepare(self.original, 'frappe/erpnext:v16.51.2')
        self.assertEqual(docs['01-backup.yaml']['services']['upgrade-job']['image'], IMAGE)
        self.assertEqual(docs['02-migrate.yaml']['services']['upgrade-job']['image'], 'frappe/erpnext:v16.51.2')

    @patch.dict(os.environ, {'EXPECTED_UPGRADE_OPERATION': OP, 'EXPECTED_UPGRADE_IMAGE': IMAGE})
    def test_fail_closed_until_migration_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with self.assertRaises(SystemExit):
                init.upgrade_guard(folder)
            state = dict(operation=OP, target=IMAGE, status='backed_up')
            p = folder / '.nas-upgrade-state.json'
            for status in ('backing_up', 'backed_up', 'migrating'):
                state['status'] = status
                p.write_text(json.dumps(state))
                with self.assertRaises(SystemExit):
                    init.upgrade_guard(folder)
            state['status'] = 'migrated'
            p.write_text(json.dumps(state))
            init.upgrade_guard(folder)
            state['operation'] = 'b' * 32
            p.write_text(json.dumps(state))
            with self.assertRaises(SystemExit):
                init.upgrade_guard(folder)

    def test_resume_preserves_database_and_scheduler_setting(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            state = dict(operation=OP, target=IMAGE, status='migrated', previous_maintenance=0, previous_pause=1)
            (folder / '.nas-upgrade-state.json').write_text(json.dumps(state))
            (folder / 'site_config.json').write_text(json.dumps(dict(db_password='keep-me', encryption_key='keep-key', maintenance_mode=1, pause_scheduler=1)))
            init.finish_upgrade(folder)
            config = json.loads((folder / 'site_config.json').read_text())
            self.assertEqual(config['db_password'], 'keep-me')
            self.assertEqual(config['encryption_key'], 'keep-key')
            self.assertEqual(config['pause_scheduler'], 1)
            self.assertEqual(config['maintenance_mode'], 0)
            self.assertEqual(json.loads((folder / '.nas-upgrade-state.json').read_text())['status'], 'resumed')


@unittest.skipIf(os.name == 'nt', 'Container-only Linux job; generator and guard tests run on Windows')
class OfflineJobTests(unittest.TestCase):
    def test_migration_failure_leaves_blocking_state(self):
        job = load('offline_job', 'upgrade_job.py')
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            try:
                os.chdir(tmp)
                folder = Path('sites/erpnext.test')
                folder.mkdir(parents=True)
                (folder / '.nas-initialized').touch()
                state_path = folder / '.nas-upgrade-state.json'
                state_path.write_text(json.dumps(dict(operation=OP, source=IMAGE, target=IMAGE, status='backed_up')))
                env = dict(SITE_NAME='erpnext.test', OPERATION_ID=OP, SOURCE_IMAGE=IMAGE,
                           TARGET_IMAGE=IMAGE, UPGRADE_PHASE='migrate', SIMULATE_FAILURE='0')
                with patch.dict(os.environ, env), patch.object(job.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'bench')):
                    with self.assertRaises(subprocess.CalledProcessError):
                        job.run_job()
                self.assertEqual(json.loads(state_path.read_text())['status'], 'migrating')
                with patch.dict(os.environ, env), patch.object(job.subprocess, 'run') as run:
                    with self.assertRaises(SystemExit):
                        job.run_job()
                    run.assert_not_called()
            finally:
                os.chdir(previous)

    def test_failure_injection_does_not_run_bench(self):
        job = load('offline_job_simulated', 'upgrade_job.py')
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            try:
                os.chdir(tmp)
                folder = Path('sites/erpnext.test')
                folder.mkdir(parents=True)
                (folder / '.nas-initialized').touch()
                state_path = folder / '.nas-upgrade-state.json'
                state_path.write_text(json.dumps(dict(operation=OP, source=IMAGE, target=IMAGE, status='backed_up')))
                env = dict(SITE_NAME='erpnext.test', OPERATION_ID=OP, SOURCE_IMAGE=IMAGE,
                           TARGET_IMAGE=IMAGE, UPGRADE_PHASE='migrate', SIMULATE_FAILURE='1')
                with patch.dict(os.environ, env), patch.object(job.subprocess, 'run') as run:
                    with self.assertRaises(SystemExit):
                        job.run_job()
                    run.assert_not_called()
                self.assertEqual(json.loads(state_path.read_text())['status'], 'backed_up')
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
