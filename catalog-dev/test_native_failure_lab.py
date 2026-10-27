"""Host helper must stay within its dedicated failure and recovery apps."""
from pathlib import Path
import json
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import native_failure_lab as lab
from native_catalog_lab import tree_hash,merge_entry,atomic,dump
from patch_policy import TARGET


class HostHelperTests(unittest.TestCase):
    def staged(self,root):
        state=root/'state'; state.mkdir()
        catalog=root/'catalog'; catalog.mkdir()
        bundle=root/'bundle'; (bundle/'recovery').mkdir(parents=True)
        app='erpnext-native-recovery-lab'
        live=catalog/'trains/community'/app; live.mkdir(parents=True)
        (live/'fixture').write_text('original app content')
        shutil.copytree(live,bundle/'recovery/source/trains/community'/app)
        entry={'healthy':True,'latest_version':'0.9.0'}
        files=tree_hash(live)
        (state/'state.json').write_text(json.dumps({'role':'source','pending':None,'entry':entry,'files':files}))
        (catalog/'catalog.json').write_text(json.dumps({'community':{app:entry}}))
        (bundle/'recovery/manifest.json').write_text(json.dumps({'entries':{'source':entry},'app_files':{'source':files}}))
        stager=SimpleNamespace(STATE=state,CATALOG=catalog,APP=app,tree_hash=tree_hash,guard_host=Mock(),refresh=Mock(),
            merge_entry=lambda data,expected,replacement: self.merge(data,app,expected,replacement),
            atomic=atomic,dump=dump,validate_catalog=Mock())
        return stager,bundle,live

    @staticmethod
    def merge(data,app,expected,replacement):
        import native_catalog_lab
        with patch.object(native_catalog_lab,'APP',app):
            return merge_entry(data,expected,replacement)

    def test_recovery_resumes_after_owned_catalog_staging_without_restaging(self):
        with tempfile.TemporaryDirectory() as tmp:
            stager,bundle,_=self.staged(Path(tmp))
            with patch.object(lab.subprocess,'run') as run:
                lab.stage_recovery_catalog(stager,bundle)
                run.assert_not_called()
            stager.refresh.assert_called_once()

    def test_recovery_rejects_external_catalog_or_file_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            stager,bundle,live=self.staged(Path(tmp))
            original=(stager.CATALOG/'catalog.json').read_text()
            (stager.CATALOG/'catalog.json').write_text(json.dumps({'community':{stager.APP:{'foreign':True}}}))
            with self.assertRaises(RuntimeError): lab.stage_recovery_catalog(stager,bundle)
            (stager.CATALOG/'catalog.json').write_text(original)
            (live/'fixture').write_text('changed externally')
            with self.assertRaises(RuntimeError): lab.stage_recovery_catalog(stager,bundle)
            stager.refresh.assert_not_called()

    def test_catalog_sync_removal_is_repaired_without_reverting_other_apps(self):
        with tempfile.TemporaryDirectory() as tmp:
            stager,bundle,live=self.staged(Path(tmp))
            journal=(stager.STATE/'state.json').read_bytes()
            shutil.rmtree(live)
            current={'community':{'another-app':{'latest_version':'9.2.1'}}}
            before=json.dumps(current).encode()
            (stager.CATALOG/'catalog.json').write_bytes(before)
            lab.stage_recovery_catalog(stager,bundle)
            updated=json.loads((stager.CATALOG/'catalog.json').read_text())
            self.assertEqual(updated['community']['another-app'],current['community']['another-app'])
            self.assertEqual(updated['community'][stager.APP]['latest_version'],'0.9.0')
            self.assertEqual(tree_hash(live),json.loads(journal)['files'])
            self.assertEqual((stager.STATE/'state.json').read_bytes(),journal)
            backups=list(stager.STATE.glob('catalog-before-restage-*.json'))
            self.assertEqual(len(backups),1)
            self.assertEqual(backups[0].read_bytes(),before)
            lab.stage_recovery_catalog(stager,bundle)
            self.assertEqual(len(list(stager.STATE.glob('catalog-before-restage-*.json'))),1)

    def test_missing_overlay_with_corrupt_bundle_is_not_repaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            stager,bundle,live=self.staged(Path(tmp))
            shutil.rmtree(live)
            (stager.CATALOG/'catalog.json').write_text('{"community":{}}')
            incoming=bundle/'recovery/source/trains/community'/stager.APP/'fixture'
            incoming.write_text('corrupted')
            with self.assertRaises(RuntimeError): lab.stage_recovery_catalog(stager,bundle)
            self.assertFalse(live.exists())
            self.assertEqual(json.loads((stager.CATALOG/'catalog.json').read_text()),{'community':{}})
            stager.refresh.assert_not_called()

    def test_concurrent_sync_change_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            stager,bundle,live=self.staged(Path(tmp))
            shutil.rmtree(live)
            index=stager.CATALOG/'catalog.json'
            index.write_text('{"community":{}}')
            original_copy=shutil.copytree
            concurrent={'community':{'new-app':{'latest_version':'2'}}}
            def raced_copy(*args,**kwargs):
                result=original_copy(*args,**kwargs)
                index.write_text(json.dumps(concurrent))
                return result
            with patch.object(lab.shutil,'copytree',side_effect=raced_copy):
                with self.assertRaises(RuntimeError): lab.stage_recovery_catalog(stager,bundle)
            self.assertFalse(live.exists())
            self.assertEqual(json.loads(index.read_text()),concurrent)

    def test_recovery_does_not_reuse_pending_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            stager,bundle,_=self.staged(Path(tmp))
            state_file=stager.STATE/'state.json'
            state=json.loads(state_file.read_text()); state['pending']={'role':'source'}
            state_file.write_text(json.dumps(state))
            with self.assertRaises(RuntimeError): lab.stage_recovery_catalog(stager,bundle)
            stager.refresh.assert_not_called()

    def test_failed_source_uses_bootstrap_and_rejects_other_app_storage(self):
        mount={'Type':'bind','Destination':'/persistent/sites',
               'Source':'/mnt/.ix-apps/app_mounts/erpnext-native-failure-test/sites'}
        with patch.object(lab,'container',return_value={'Mounts':[mount]}) as container:
            self.assertEqual(lab.sites(lab.FAILURE,running=False),Path(mount['Source']))
            container.assert_called_once_with(lab.FAILURE,'bootstrap',False)
            mount['Source']='/mnt/.ix-apps/app_mounts/erpnext-native-test/sites'
            with self.assertRaises(RuntimeError): lab.sites(lab.FAILURE,running=False)

    def test_fixture_refuses_target_image_before_writing_data(self):
        with patch.object(lab,'app'), patch.object(lab,'container',return_value={'Config':{'Image':TARGET}}), patch.object(lab,'execute') as execute:
            with self.assertRaises(RuntimeError): lab.fixture()
            execute.assert_not_called()

    def test_recovery_never_replaces_existing_destination(self):
        with patch.object(lab,'failed',return_value=(Path('/source'),Path('/source/backup'))), patch.object(lab,'call',return_value=[{'name':lab.RECOVERY}]), patch.object(lab.subprocess,'run') as run:
            with self.assertRaises(RuntimeError): lab.recover()
            run.assert_not_called()


if __name__=='__main__': unittest.main()
