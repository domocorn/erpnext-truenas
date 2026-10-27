"""Verified private backup copy and the actual TrueNAS forbidden-path render case."""
import argparse
import json
from pathlib import Path
import stat
import sys
import unittest
from unittest.mock import patch
import yaml
import native_failure_lab as lab
import test_native_restore as restore_tests
from native_policy import operation_id
from patch_policy import TARGET
from build_native_candidate import build
from render_catalog import render

parser=argparse.ArgumentParser()
parser.add_argument('--apps-root',type=Path,required=True)
args,remaining=parser.parse_known_args()
sys.argv=[sys.argv[0],*remaining]


class RecoveryInputTests(unittest.TestCase):
    def setUp(self):
        self.fixture=restore_tests.NativeRestoreTests()
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.source=self.fixture.input
        manifest_path=self.source/'manifest.json'
        manifest=json.loads(manifest_path.read_text())
        manifest['operation']=operation_id(lab.SITE,TARGET)
        manifest_path.write_text(json.dumps(manifest))
        self.base=self.source.parent/'private-input'
        p=patch.object(lab,'RECOVERY_INPUT',self.base)
        p.start(); self.addCleanup(p.stop)

    def test_copy_is_verified_readable_by_frappe_and_reused_without_source_changes(self):
        before={p.name:p.read_bytes() for p in self.source.iterdir()}
        destination=lab.prepare_recovery_input(self.source)
        self.assertEqual(destination.parent,self.base)
        self.assertEqual(destination.stat().st_uid,1000)
        self.assertEqual(stat.S_IMODE(destination.stat().st_mode),0o500)
        for path in destination.iterdir():
            self.assertEqual(path.stat().st_uid,1000)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o400)
            self.assertEqual(path.read_bytes(),before[path.name])
        self.assertEqual(lab.prepare_recovery_input(self.source),destination)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.source.iterdir()})
        (destination/'fixture-database.sql.gz').chmod(0o600)
        (destination/'fixture-database.sql.gz').write_bytes(b'corrupted copy')
        with self.assertRaises(RuntimeError): lab.prepare_recovery_input(self.source)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.source.iterdir()})

    def test_unknown_directory_or_symlink_is_preserved(self):
        self.base.mkdir()
        marker=self.base/'unrelated'; marker.write_text('preserve me')
        with self.assertRaises(RuntimeError): lab.prepare_recovery_input(self.source)
        self.assertEqual(marker.read_text(),'preserve me')
        marker.unlink(); self.base.rmdir()
        self.base.symlink_to(self.source,target_is_directory=True)
        with self.assertRaises(RuntimeError): lab.prepare_recovery_input(self.source)

    def test_actual_template_rejects_internal_backup_and_mounts_lab_copy_readonly(self):
        candidate=self.source.parent/'candidate'
        build(args.apps_root.resolve(),candidate,'source','recovery')
        app=candidate/'ix-dev/community/erpnext-native-recovery-lab'
        values=yaml.safe_load((app/'ix_values.yaml').read_text())
        values.update(yaml.safe_load((app/'templates/test_values/basic-values.yaml').read_text()))
        values['ix_context']={'app_name':lab.RECOVERY,'app_metadata':{'title':'Recovery','train':'community'}}
        values['erpnext']['recovery_path']='/mnt/.ix-apps/app_mounts/erpnext-native-failure-test/sites/.catalog-recovery/'+operation_id(lab.SITE,TARGET)
        with self.assertRaisesRegex(Exception,'not allowed to be mounted'):
            render(values,candidate,'erpnext-native-recovery-lab')
        allowed='/mnt/labpool/erpnext-native-recovery-input-01/'+operation_id(lab.SITE,TARGET)
        values['erpnext']['recovery_path']=allowed
        document=render(values,candidate,'erpnext-native-recovery-lab')
        mounts=[m for m in document['services']['initializer']['volumes'] if m.get('target')=='/recovery']
        self.assertEqual(len(mounts),1)
        self.assertEqual(mounts[0]['source'],allowed)
        self.assertTrue(mounts[0]['read_only'])
        self.assertFalse(mounts[0]['bind']['create_host_path'])


if __name__=='__main__': unittest.main()
