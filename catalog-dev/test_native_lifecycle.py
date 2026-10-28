"""Integrated fresh-install, automatic source detection and fail-closed native state."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import test_rehearsal as rehearsal_tests
from native_policy import operation_id
from patch_policy import SOURCE,TARGET
import patch_target


class NativeTests(rehearsal_tests.RehearsalTests):
    def native(self,image=TARGET):
        os.environ['CATALOG_IMAGE']=image
        spec=importlib.util.spec_from_file_location('native_test',Path(__file__).with_name('native_lifecycle.py'))
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'rehearsal':self.job}): spec.loader.exec_module(module)
        return module

    def source_state(self):
        (self.root/'.catalog-image').write_text(SOURCE)
        self.job.write_json(self.root/self.site/'.nas-upgrade-state.json',dict(layout='catalog-native-v1',
            installation='fresh',operation=operation_id(self.site,SOURCE),source=SOURCE,target=SOURCE,status='resumed'))

    def test_fresh_install_and_repeat_need_no_backup_or_manual_operation(self):
        native=self.native()
        (self.root/'.catalog-image').write_text(TARGET)
        marker=self.root/self.site/'.nas-initialized'
        marker.unlink()
        def install():
            if not marker.exists():
                self.assertNotIn('EXPECTED_UPGRADE_OPERATION',os.environ)
                marker.touch()
        native.backup(self.root)
        native.initialize(self.root,install)
        self.assertEqual(self.state()['operation'],operation_id(self.site,TARGET))
        self.assertEqual(self.state()['installation'],'fresh')
        native.backup(self.root)
        native.initialize(self.root,install)
        self.assertFalse((self.root/'.catalog-recovery').exists())

    def test_native_source_backup_target_commit_and_repeat(self):
        native=self.native()
        self.source_state()
        baked=self.root/'baked-assets'; baked.mkdir()
        (self.root/'assets').symlink_to(baked,target_is_directory=True)
        version=SimpleNamespace(__version__='16.51.1')
        with patch.dict(sys.modules,{'erpnext':version}),patch.object(self.job.subprocess,'run',self.command),patch.object(patch_target,'BAKED',baked):
            native.backup(self.root)
            self.assertEqual(self.state()['status'],'backed_up')
            version.__version__='16.52.1'
            native.initialize(self.root,lambda:None)
            native.backup(self.root)
            native.initialize(self.root,lambda:None)
        self.assertEqual((self.root/'.catalog-image').read_text().strip(),TARGET)
        self.assertEqual(self.state()['operation'],operation_id(self.site,TARGET))
        self.assertEqual(self.state()['status'],'resumed')
        self.assertEqual(sum('migrate' in call for call in self.calls),1)

    def test_partial_native_migration_blocks_backup_and_resume(self):
        native=self.native()
        self.source_state()
        version=SimpleNamespace(__version__='16.51.1')
        initialize=Mock()
        with patch.dict(sys.modules,{'erpnext':version}),patch.object(self.job.subprocess,'run',self.command):
            native.backup(self.root)
            version.__version__='16.52.1'
            with patch.object(self.job.subprocess,'run',side_effect=subprocess.CalledProcessError(1,'bench')):
                with self.assertRaises(subprocess.CalledProcessError): native.initialize(self.root,initialize)
            self.assertEqual(self.state()['status'],'migrating')
            version.__version__='16.51.1'
            with self.assertRaises(RuntimeError): native.backup(self.root)
            version.__version__='16.52.1'
            with self.assertRaises(RuntimeError): native.initialize(self.root,initialize)
        initialize.assert_not_called()
        self.assertEqual((self.root/'.catalog-image').read_text(),SOURCE)

    def test_downgrade_and_unmanaged_initialized_state_are_refused(self):
        native=self.native(SOURCE)
        (self.root/'.catalog-image').write_text(TARGET)
        with self.assertRaises(RuntimeError): native.bootstrap(self.root)
        os.environ['CATALOG_IMAGE']=TARGET
        with patch.dict(sys.modules,{'erpnext':SimpleNamespace(__version__='16.52.1')}):
            with self.assertRaises(RuntimeError): native.initialize(self.root,Mock())


if __name__=='__main__': unittest.main()
