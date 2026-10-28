"""Exact-pair policy, source/target phases and durable patch commit guards."""
import copy
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import yaml
import test_rehearsal as rehearsal_tests
import patch_target
from patch_policy import SOURCE, TARGET, SOURCE_DIGEST, SOURCE_ID, validate_patch
from prepare_patch import prepare
from render_catalog import render_legacy as render


class PatchTests(rehearsal_tests.RehearsalTests):
    def patch_source(self):
        (self.root/'.catalog-image').write_text(SOURCE)
        os.environ.update(SOURCE_IMAGE=SOURCE,TARGET_IMAGE=TARGET,SOURCE_DIGEST=SOURCE_DIGEST,
            OBSERVED_SOURCE_IMAGE_ID=SOURCE_ID,CATALOG_OPERATION_LAYOUT='catalog-patch-v1',UPGRADE_PHASE='backup')
        return patch.dict('sys.modules',{'erpnext':SimpleNamespace(__version__='16.51.1')})

    def test_exact_pair_policy_refuses_unreviewed_images(self):
        validate_patch(SOURCE,TARGET,SOURCE_DIGEST,SOURCE_ID)
        for values in ((TARGET,SOURCE,SOURCE_DIGEST,SOURCE_ID),
                (SOURCE,TARGET.replace('16.52.1','16.51.2'),SOURCE_DIGEST,SOURCE_ID),
                (SOURCE,TARGET,SOURCE_DIGEST,'sha256:'+'0'*64),
                (SOURCE.split('@')[0],TARGET,SOURCE_DIGEST,SOURCE_ID)):
            with self.assertRaises(RuntimeError): validate_patch(*values)

    def test_source_backup_target_migration_commit_and_repeat(self):
        import sys
        baked=self.root/'baked-assets'
        baked.mkdir()
        (self.root/'assets').symlink_to(baked,target_is_directory=True)
        with self.patch_source(),patch.object(self.job.subprocess,'run',self.command),patch.object(patch_target,'BAKED',baked):
            self.job.run_job()
            self.assertEqual(self.state()['source'],SOURCE)
            self.assertEqual(self.state()['target'],TARGET)
            sys.modules['erpnext'].__version__='16.52.1'
            def initialize():
                self.assertEqual((self.root/'.catalog-image').read_text().strip(),TARGET)
                self.assertIn(self.state()['status'],('migrated','resumed'))
            patch_target.finish(self.job,initialize)
            patch_target.finish(self.job,initialize)
            self.assertEqual(self.state()['status'],'resumed')
            self.assertEqual(sum('migrate' in command for command in self.calls),1)
            sys.modules['erpnext'].__version__='16.51.1'
            os.environ['UPGRADE_PHASE']='backup'
            self.job.run_job()
            os.environ['OPERATION_ID']='d'*32
            with self.assertRaisesRegex(RuntimeError,'Source image marker'):
                self.job.run_job()

    def test_wrong_phase_image_and_corrupt_backup_cannot_commit(self):
        import sys
        with self.patch_source(),patch.object(self.job.subprocess,'run',self.command):
            self.job.run_job()
            os.environ['UPGRADE_PHASE']='migrate'
            with self.assertRaisesRegex(RuntimeError,'version differs'):
                self.job.run_job()
            sys.modules['erpnext'].__version__='16.52.1'
            backup=self.root/'.catalog-recovery'/('a'*32)/'fixture-database.sql.gz'
            backup.write_bytes(b'corrupt')
            with self.assertRaisesRegex(RuntimeError,'integrity'):
                patch_target.finish(self.job,lambda:None)
            self.assertEqual((self.root/'.catalog-image').read_text(),SOURCE)
            self.assertEqual(self.state()['status'],'backed_up')

    def test_graph_uses_old_backup_new_target_and_preserves_dependencies(self):
        args=rehearsal_tests.args
        app=args.apps_root/'ix-dev/community/erpnext'
        values=yaml.safe_load((app/'ix_values.yaml').read_text())
        values['images']['image']['tag']=SOURCE.split(':',1)[1]
        values.update(yaml.safe_load((app/'templates/test_values/basic-values.yaml').read_text()))
        values['ix_context']={'app_name':'erpnext-catalog-patch-test','app_metadata':{'title':'ERPNext','train':'community'}}
        source=render(values,args.apps_root)
        source['networks']={'default':{'name':'ix-erpnext-catalog-patch-test_default'}}
        before=copy.deepcopy(source)
        result=prepare(source)
        self.assertEqual(source,before)
        self.assertEqual(result['services']['patch-backup']['image'],SOURCE)
        self.assertEqual(result['services']['initializer']['image'],TARGET)
        self.assertEqual(result['services']['initializer']['depends_on']['patch-backup']['condition'],'service_completed_successfully')
        self.assertEqual(result['services']['backend']['depends_on']['initializer']['condition'],'service_completed_successfully')
        for name in ('db','redis-cache','redis-queue','permissions'):
            self.assertEqual(result['services'][name],source['services'][name])
        from prepare_patch_recovery import prepare as recover
        recovered=recover(result,args.apps_root,'/mnt/labpool/patch-recovery')
        self.assertEqual(recovered['03-start-restored-clone.yaml']['services']['backend']['image'],SOURCE)
        self.assertNotEqual(recovered['03-start-restored-clone.yaml']['networks'],result['networks'])
        source['networks']['default']['name']='working-recovery-app'
        with self.assertRaises(ValueError): prepare(source)

    def test_patch_backup_restores_only_with_source_version(self):
        import restore_job
        with self.patch_source(),patch.object(self.job.subprocess,'run',self.command):
            self.job.run_job()
        folder=self.root/'.catalog-recovery'/('a'*32)
        with patch.object(restore_job,'INPUT',folder):
            self.assertEqual(len(restore_job.inventory(SOURCE,'a'*32)),4)
            with self.assertRaisesRegex(RuntimeError,'source image'):
                restore_job.inventory(TARGET,'a'*32)
            manifest=json.loads((folder/'manifest.json').read_text())
            manifest['target']=TARGET.replace('16.52.1','16.51.2')
            (folder/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(RuntimeError): restore_job.inventory(SOURCE,'a'*32)

    def test_failed_target_migration_keeps_source_marker_and_blocks_retry(self):
        import sys
        from unittest.mock import Mock
        with self.patch_source(),patch.object(self.job.subprocess,'run',self.command):
            self.job.run_job()
            sys.modules['erpnext'].__version__='16.52.1'
            initialize=Mock()
            with patch.object(self.job.subprocess,'run',side_effect=subprocess.CalledProcessError(1,'bench')) as command:
                with self.assertRaises(subprocess.CalledProcessError): patch_target.finish(self.job,initialize)
                self.assertEqual(self.state()['status'],'migrating')
                self.assertEqual((self.root/'.catalog-image').read_text(),SOURCE)
                with self.assertRaises(RuntimeError): patch_target.finish(self.job,initialize)
                self.assertEqual(command.call_count,1)
            initialize.assert_not_called()


if __name__=='__main__': unittest.main()
