"""Native restore state, independent encryption identity and interrupted retry refusal."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import restore_job as job
from native_policy import operation_id
from patch_policy import SOURCE,TARGET,SOURCE_DIGEST,SOURCE_ID


class NativeRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.sites=root/'sites'; self.sites.mkdir()
        self.input=root/'backup'; self.input.mkdir()
        self.site='erpnext.localhost'
        self.folder=self.sites/self.site; self.folder.mkdir()
        (self.folder/'.nas-initialized').touch()
        (self.sites/'.catalog-site-name').write_text(self.site)
        (self.sites/'.catalog-image').write_text(SOURCE)
        job.write_json(self.folder/'site_config.json',{'db_name':'independent_destination','encryption_key':'fresh-key'})
        job.write_json(self.folder/'.nas-upgrade-state.json',dict(layout='catalog-native-v1',installation='fresh',
            operation=operation_id(self.site,SOURCE),source=SOURCE,target=SOURCE,status='resumed'))
        names=['fixture-database.sql.gz','fixture-files.tar','fixture-private-files.tar',
            'fixture-site_config_backup.json','other-1','other-2','other-3','other-4']
        files={}
        for name in names:
            data=json.dumps({'encryption_key':'preserved-source-key'}).encode() if name.endswith('.json') else b'fixture'
            (self.input/name).write_bytes(data)
            files[name]={'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        job.write_json(self.input/'manifest.json',dict(layout='catalog-patch-v1',operation='b'*32,
            status='backed_up',source=SOURCE,target=TARGET,source_digest=SOURCE_DIGEST,
            observed_source_image_id=SOURCE_ID,backup_files=files))
        for name,value in [('ROOT',self.sites),('INPUT',self.input)]:
            p=patch.object(job,name,value); p.start(); self.addCleanup(p.stop)
        p=patch.dict(os.environ,dict(SITE_NAME=self.site,RESTORE_OPERATION='c'*32,
            CATALOG_IMAGE=SOURCE,DESTINATION_APP='erpnext-native-recovery-test',
            NATIVE_RESTORE_ACK='disposable-native-recovery',BACKUP_OPERATION='b'*32,
            DEST_DB_ROOT_PASSWORD='fictional-db-password'))
        p.start(); self.addCleanup(p.stop)

    def state(self):
        return json.loads((self.folder/'.nas-upgrade-state.json').read_text())

    def test_native_restore_keeps_database_identity_and_repeats_without_restore(self):
        with patch.object(job.subprocess,'run') as run:
            job.run(native=True)
            self.assertEqual(run.call_count,2)
            job.run(native=True)
            self.assertEqual(run.call_count,2)
        config=json.loads((self.folder/'site_config.json').read_text())
        self.assertEqual(config['db_name'],'independent_destination')
        self.assertEqual(config['encryption_key'],'preserved-source-key')
        self.assertEqual(config['pause_scheduler'],1)
        self.assertEqual(self.state()['layout'],'catalog-native-v1')
        self.assertEqual(self.state()['restoration'],'c'*32)

    def test_native_restore_failure_persists_blocking_state(self):
        with patch.object(job.subprocess,'run',side_effect=subprocess.CalledProcessError(1,'bench')):
            with self.assertRaises(subprocess.CalledProcessError): job.run(native=True)
        self.assertEqual(self.state()['status'],'restoring')
        with patch.object(job.subprocess,'run') as run:
            with self.assertRaises(RuntimeError): job.run(native=True)
            run.assert_not_called()

    def test_native_ack_and_exact_source_are_required(self):
        with patch.dict(os.environ,{'NATIVE_RESTORE_ACK':''}):
            with self.assertRaises(RuntimeError): job.run(native=True)
        with patch.dict(os.environ,{'CATALOG_IMAGE':TARGET}):
            with self.assertRaises(RuntimeError): job.run(native=True)
        with self.assertRaises(RuntimeError): job.run()


if __name__=='__main__': unittest.main()
