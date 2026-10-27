"""State-machine and preservation tests for catalog-layout rehearsal plans."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yaml
from prepare_rehearsal import prepare
from render_catalog import render_legacy as render

parser = argparse.ArgumentParser()
parser.add_argument('--apps-root', required=True, type=Path)
args, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0], *remaining]


class RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = 'test.local'
        folder = self.root / self.site
        folder.mkdir()
        (folder / '.nas-initialized').touch()
        self.image = 'frappe/erpnext:v16.51.1'
        (self.root / '.catalog-image').write_text(self.image)
        (self.root / '.catalog-site-name').write_text(self.site)
        (self.root / 'common_site_config.json').write_text('{"db_host":"db"}')
        (folder / 'site_config.json').write_text('{"maintenance_mode":0,"pause_scheduler":1,"db_password":"keep-test-secret"}')
        spec = importlib.util.spec_from_file_location('rehearsal_job_test', Path(__file__).with_name('rehearsal_job.py'))
        self.job = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'fcntl': SimpleNamespace(flock=lambda *a: None, LOCK_EX=1, LOCK_NB=4)} if os.name == 'nt' else {}):
            spec.loader.exec_module(self.job)
        self.job.ROOT = self.root
        self.job.assert_queue_quiescent = lambda: None  # Queue behavior is tested separately.
        # fsync of directory handles is a Linux runtime operation.
        if os.name == 'nt':
            def write_json(path, value):
                path.write_text(json.dumps(value))
            self.job.write_json = write_json
            # Windows cannot fsync the read-only handles used by Linux runtime.
            synchronization = patch.object(self.job.os, 'fsync', lambda descriptor: None)
            synchronization.start()
            self.addCleanup(synchronization.stop)
        self.environment = dict(SITE_NAME=self.site, OPERATION_ID='a' * 32,
            SOURCE_IMAGE=self.image, TARGET_IMAGE=self.image, UPGRADE_PHASE='backup', SIMULATE_FAILURE='0')
        self.environment_patch = patch.dict(os.environ, self.environment)
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)
        self.calls = []

    def command(self, arguments, **kwargs):
        self.calls.append(arguments)
        if 'backup' in arguments:
            recovery = Path(arguments[arguments.index('--backup-path') + 1])
            for suffix in ('database.sql.gz', 'files.tar', 'private-files.tar', 'site_config_backup.json'):
                (recovery / ('fixture-' + suffix)).write_bytes(b'backup-test-data')

    def state(self):
        return json.loads((self.root / self.site / '.nas-upgrade-state.json').read_text())

    def test_simulated_failure_then_migration_and_repeat_guards(self):
        with patch.object(self.job.subprocess, 'run', self.command):
            self.job.run_job()
            self.job.run_job()
            self.assertEqual(len(self.calls), 1)
            self.assertEqual(self.state()['previous_pause'], 1)
            os.environ.update(UPGRADE_PHASE='migrate', SIMULATE_FAILURE='1')
            with self.assertRaises(RuntimeError): self.job.run_job()
            self.assertEqual(self.state()['status'], 'backed_up')
            os.environ['SIMULATE_FAILURE'] = '0'
            self.job.run_job()
            self.job.run_job()
            self.assertEqual(self.state()['status'], 'migrated')
            self.assertEqual(sum('migrate' in call for call in self.calls), 1)

    def test_interrupted_migration_cannot_retry(self):
        with patch.object(self.job.subprocess, 'run', self.command): self.job.run_job()
        os.environ['UPGRADE_PHASE'] = 'migrate'
        with patch.object(self.job.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'bench')) as run:
            with self.assertRaises(subprocess.CalledProcessError): self.job.run_job()
            self.assertEqual(self.state()['status'], 'migrating')
            with self.assertRaises(RuntimeError): self.job.run_job()
            self.assertEqual(run.call_count, 1)

    def test_corrupt_backup_blocks_migration(self):
        with patch.object(self.job.subprocess, 'run', self.command): self.job.run_job()
        (self.root / '.catalog-recovery' / ('a' * 32) / 'fixture-database.sql.gz').write_bytes(b'corrupt')
        os.environ['UPGRADE_PHASE'] = 'migrate'
        with patch.object(self.job.subprocess, 'run') as run:
            with self.assertRaises(RuntimeError): self.job.run_job()
            run.assert_not_called()
        self.assertEqual(self.state()['status'], 'backed_up')

    def test_image_change_and_wrong_operation_are_refused(self):
        os.environ['TARGET_IMAGE'] = 'frappe/erpnext:v16.51.2'
        with self.assertRaises(RuntimeError): self.job.run_job()
        os.environ['TARGET_IMAGE'] = self.image
        with patch.object(self.job.subprocess, 'run', self.command): self.job.run_job()
        os.environ.update(OPERATION_ID='b' * 32, UPGRADE_PHASE='migrate')
        with self.assertRaises(RuntimeError): self.job.run_job()

    def test_plan_preserves_storage_secrets_images_and_gates_runtime(self):
        app = args.apps_root / 'ix-dev/community/erpnext'
        values = yaml.safe_load((app / 'ix_values.yaml').read_text())
        values['images']['image']['tag'] = 'v16.51.1'  # Installed legacy baseline.
        values.update(yaml.safe_load((app / 'templates/test_values/basic-values.yaml').read_text()))
        values['ix_context'] = {'app_name': 'test', 'app_metadata': {'title': 'ERPNext', 'train': 'community'}}
        original = render(values, args.apps_root)
        unchanged = copy.deepcopy(original)
        outputs = prepare(original, 'a' * 32)
        self.assertEqual(original, unchanged)
        self.assertEqual(len(outputs), 5)
        for filename, document in outputs.items():
            for name in ('db', 'redis-cache', 'redis-queue', 'permissions'):
                self.assertEqual(document['services'][name], original['services'][name])
            for service in document['services'].values():
                if service.get('image', '').startswith('frappe/erpnext:'):
                    self.assertEqual(service['image'], self.image)
            if filename.startswith(('01', '02', '04')):
                self.assertFalse(set(('backend', 'frontend', 'websocket', 'scheduler', 'queue-short', 'queue-long')) & document['services'].keys())
                self.assertEqual(document['services']['rehearsal-job']['volumes'], original['services']['backend']['volumes'])
            else:
                for name in ('backend', 'frontend', 'websocket', 'scheduler', 'queue-short', 'queue-long'):
                    self.assertEqual(document['services'][name]['volumes'], original['services'][name]['volumes'])
                    self.assertEqual(document['services'][name]['environment']['EXPECTED_UPGRADE_OPERATION'], 'a' * 32)
        del original['configs']['catalog_runtime']
        with self.assertRaises(ValueError): prepare(original)


if __name__ == '__main__':
    unittest.main()
