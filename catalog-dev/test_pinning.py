"""Pinning preserves deployment settings and refuses unsafe image/state changes."""
import copy
import os
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import yaml
import test_rehearsal as rehearsal_tests
from prepare_pinning import prepare
from prepare_restore import prepare as restore
from prepare_rehearsal import prepare as rehearsal
from prepare_healthcheck_update import RUNTIME
from render_catalog import render_legacy as render

DIGEST = 'sha256:' + 'b' * 64
IMAGE_ID = 'sha256:' + 'c' * 64


class PinningTests(rehearsal_tests.RehearsalTests):
    def upgrade_environment(self):
        os.environ.update(CATALOG_OPERATION_LAYOUT='catalog-upgrade-v1',
            SOURCE_DIGEST=DIGEST, OBSERVED_SOURCE_IMAGE_ID=IMAGE_ID,
            TARGET_IMAGE=self.image + '@' + DIGEST)
        return patch.dict(sys.modules, {'erpnext': SimpleNamespace(__version__='16.51.1')})

    def test_same_content_backup_migrate_and_marker_checks(self):
        with self.upgrade_environment(), patch.object(self.job.subprocess, 'run', self.command):
            self.job.run_job()
            self.assertEqual(self.state()['target'], self.image + '@' + DIGEST)
            self.assertEqual(self.state()['observed_source_image_id'], IMAGE_ID)
            os.environ['UPGRADE_PHASE'] = 'migrate'
            self.job.run_job()
            (self.root / '.catalog-image').write_text(self.image + '@' + DIGEST)
            self.job.identities(allow_target=True)
            with self.assertRaisesRegex(RuntimeError, 'Image identity'):
                self.job.identities()

    def test_previous_restore_must_be_successful_and_match(self):
        with self.upgrade_environment():
            previous = dict(layout='catalog-restore-v1', operation='d'*32, target=self.image, status='restoring')
            path = self.root / self.site / '.nas-upgrade-state.json'
            self.job.write_json(path, previous)
            os.environ['PREVIOUS_UPGRADE_OPERATION'] = 'd'*32
            with self.assertRaisesRegex(RuntimeError, 'expected successful'):
                self.job.run_job()
            previous['status'] = 'resumed'
            previous['operation'] = 'e'*32
            self.job.write_json(path, previous)
            with self.assertRaisesRegex(RuntimeError, 'expected successful'):
                self.job.run_job()
            previous['operation'] = 'd'*32
            self.job.write_json(path, previous)
            with patch.object(self.job.subprocess, 'run', self.command):
                self.job.run_job()

    def test_invalid_transitions_are_rejected(self):
        for target in (self.image, self.image + '@sha256:' + 'f'*64,
                'frappe/erpnext:v16.50.9@' + DIGEST, 'frappe/erpnext:v17.0.0@' + DIGEST):
            with self.assertRaises(RuntimeError):
                self.job.validate_transition(self.image, target, DIGEST, IMAGE_ID)

    def test_plan_preserves_storage_credentials_and_dependencies(self):
        args = rehearsal_tests.args
        app = args.apps_root / 'ix-dev/community/erpnext'
        values = yaml.safe_load((app/'ix_values.yaml').read_text())
        values['images']['image']['tag'] = 'v16.51.1'  # Installed legacy baseline.
        values.update(yaml.safe_load((app/'templates/test_values/basic-values.yaml').read_text()))
        for name in ('sites', 'logs', 'db_data', 'queue_data'):
            values['storage'][name] = {'type':'host_path','host_path_config':{
                'path':'/mnt/labpool/source/'+name,'auto_permissions':True}}
        values['ix_context'] = {'app_name':'source','app_metadata':{'title':'ERPNext','train':'community'}}
        source = rehearsal(render(values,args.apps_root),'a'*32)['05-resume.yaml']
        clone = restore(source,args.apps_root,'/mnt/labpool/restore')['03-start-restored-clone.yaml']
        before = copy.deepcopy(clone)
        outputs = prepare(clone,DIGEST,IMAGE_ID,'f'*32)
        self.assertEqual(before,clone)
        for document in outputs.values():
            for name in ('db','redis-cache','redis-queue','permissions'):
                self.assertEqual(document['services'][name],clone['services'][name])
            self.assertEqual(document['networks'],clone['networks'])
        resumed = outputs['05-resume.yaml']
        for name in RUNTIME:
            self.assertEqual(resumed['services'][name]['volumes'],clone['services'][name]['volumes'])
            self.assertEqual(resumed['services'][name]['image'],self.image+'@'+DIGEST)
        self.assertEqual(resumed['services']['initializer']['environment']['DB_ROOT_PASSWORD'],
            clone['services']['initializer']['environment']['DB_ROOT_PASSWORD'])
        with self.assertRaises(ValueError): prepare(source,DIGEST,IMAGE_ID)


if __name__ == '__main__':
    unittest.main()
