"""Isolation and source-checksum tests for catalog restore preparation."""
import argparse
import copy
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import yaml
from prepare_restore import prepare
from prepare_rehearsal import prepare as rehearsal
from render_catalog import render_legacy as render

parser=argparse.ArgumentParser()
parser.add_argument('--apps-root',required=True,type=Path)
args,remaining=parser.parse_known_args()
sys.argv=[sys.argv[0],*remaining]


class RestoreTests(unittest.TestCase):
    def source(self):
        app=args.apps_root/'ix-dev/community/erpnext'
        values=yaml.safe_load((app/'ix_values.yaml').read_text())
        for image in values['images'].values():
            image['tag']=image['tag'].split('@')[0] if image['repository'] in ('frappe/erpnext','mariadb','redis') else image['tag']
        values.update(yaml.safe_load((app/'templates/test_values/basic-values.yaml').read_text()))
        for name in ('sites','logs','db_data','queue_data'):
            values['storage'][name]={'type':'host_path','host_path_config':{'path':'/mnt/labpool/source/'+name,'auto_permissions':True}}
        values['ix_context']={'app_name':'source','app_metadata':{'title':'ERPNext','train':'community'}}
        return rehearsal(render(values,args.apps_root),'a'*32)['05-resume.yaml']

    def test_plan_isolates_destination_and_mounts_backup_readonly(self):
        source=self.source()
        before=copy.deepcopy(source)
        documents=prepare(source,args.apps_root,'/mnt/labpool/restore')
        self.assertEqual(source,before)
        self.assertEqual(len(documents),3)
        job=documents['02-restore-clone.yaml']['services']['restore-job']
        backup=[m for m in job['volumes'] if m['target']=='/recovery'][0]
        self.assertTrue(backup['read_only'])
        self.assertFalse(backup['bind']['create_host_path'])
        for document in documents.values():
            for name,service in document['services'].items():
                for mount in service.get('volumes',[]):
                    if mount['target']!='/recovery':
                        self.assertTrue(mount['source'].startswith('/mnt/labpool/restore/'))
            self.assertNotEqual(document['networks'],source.get('networks', {}))
        self.assertNotEqual(documents['01-initialize-clone.yaml']['services']['db']['environment']['MARIADB_ROOT_PASSWORD'],source['services']['db']['environment']['MARIADB_ROOT_PASSWORD'])
        self.assertNotIn('backend',documents['02-restore-clone.yaml']['services'])

    def test_overlapping_storage_and_ports_are_rejected(self):
        source=self.source()
        for root in ('/mnt/labpool/source','/mnt/labpool/source/sites/subdir','/mnt/labpool','/mnt/labpool/../source'):
            with self.assertRaises(ValueError): prepare(source,args.apps_root,root)
        with self.assertRaises(ValueError): prepare(source,args.apps_root,'/mnt/labpool/restore',18084)

    def test_corrupt_backup_is_refused_before_restore(self):
        spec=importlib.util.spec_from_file_location('restore_job_test',Path(__file__).with_name('restore_job.py'))
        job=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'fcntl':SimpleNamespace()} if os.name=='nt' else {}): spec.loader.exec_module(job)
        with tempfile.TemporaryDirectory() as tmp:
            job.INPUT=Path(tmp)
            files={}
            for index in range(8):
                name='fixture-'+str(index)
                (job.INPUT/name).write_bytes(b'wrong')
                files[name]={'size':5,'sha256':'0'*64}
            manifest=dict(layout='catalog-rehearsal-v1',operation='a'*32,source='image',target='image',status='backed_up',backup_files=files)
            (job.INPUT/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(RuntimeError,'checksum'): job.inventory('image','a'*32)
            with self.assertRaisesRegex(RuntimeError,'identity'): job.inventory('image','b'*32)

    def test_pinned_restore_keeps_digest_and_separates_source(self):
        from prepare_pinning import prepare as pinning
        clone = prepare(self.source(),args.apps_root,'/mnt/labpool/restore')['03-start-restored-clone.yaml']
        source = pinning(clone,'sha256:'+'b'*64,'sha256:'+'c'*64)['05-resume.yaml']
        before = copy.deepcopy(source)
        documents = prepare(source,args.apps_root,'/mnt/labpool/pinned-recovery',18086,
            'erpnext-catalog-pinned-recovery-test')
        self.assertEqual(source,before)
        for document in documents.values():
            self.assertNotEqual(document['networks'],source['networks'])
            for service in document['services'].values():
                if service['image'].startswith('frappe/erpnext:'):
                    self.assertEqual(service['image'],source['services']['backend']['image'])
        with self.assertRaisesRegex(ValueError,'network'):
            prepare(source,args.apps_root,'/mnt/labpool/pinned-recovery',18086)

    def test_pinning_manifest_accepts_only_proven_same_content(self):
        spec=importlib.util.spec_from_file_location('restore_pinning_test',Path(__file__).with_name('restore_job.py'))
        job=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'fcntl':SimpleNamespace()} if os.name=='nt' else {}): spec.loader.exec_module(job)
        with tempfile.TemporaryDirectory() as tmp:
            job.INPUT=Path(tmp)
            names=['fixture-'+suffix for suffix in ('database.sql.gz','files.tar','private-files.tar','site_config_backup.json')]
            names += ['site_config.before.json','common_site_config.before.json','catalog-site-name.before','catalog-image.before']
            files={}
            for name in names:
                (job.INPUT/name).write_bytes(b'fixture')
                files[name]={'size':7,'sha256':hashlib.sha256(b'fixture').hexdigest()}
            image='frappe/erpnext:v16.51.1@sha256:'+'b'*64
            manifest=dict(layout='catalog-upgrade-v1',operation='a'*32,source='frappe/erpnext:v16.51.1',
                target=image,status='backed_up',source_digest='sha256:'+'b'*64,
                observed_source_image_id='sha256:'+'c'*64,backup_files=files)
            path=job.INPUT/'manifest.json'
            path.write_text(json.dumps(manifest))
            self.assertEqual(set(job.inventory(image,'a'*32)),{'database','public','private','config'})
            for key,value in [('source','frappe/erpnext:v16.50.0'),('source_digest','sha256:'+'d'*64),
                    ('observed_source_image_id',''),('layout','future-layout'),('status','migrating')]:
                invalid=dict(manifest,**{key:value})
                path.write_text(json.dumps(invalid))
                with self.assertRaises(RuntimeError): job.inventory(image,'a'*32)

    def test_interrupted_restore_refuses_retry_before_database_commands(self):
        spec=importlib.util.spec_from_file_location('restore_interrupted_test',Path(__file__).with_name('restore_job.py'))
        job=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'fcntl':SimpleNamespace(flock=lambda *a:None,LOCK_EX=1,LOCK_NB=4)} if os.name=='nt' else {}):
            spec.loader.exec_module(job)
        with tempfile.TemporaryDirectory() as tmp:
            job.ROOT=Path(tmp)
            site=job.ROOT/'test.local'
            site.mkdir()
            (job.ROOT/'.catalog-site-name').write_text('test.local')
            (job.ROOT/'.catalog-image').write_text('frappe/erpnext:v16.51.1')
            (site/'.nas-initialized').touch()
            state={'layout':'catalog-restore-v1','operation':'a'*32,'status':'restoring'}
            (site/'.nas-upgrade-state.json').write_text(json.dumps(state))
            environment=dict(SITE_NAME='test.local',RESTORE_OPERATION='a'*32,
                CATALOG_IMAGE='frappe/erpnext:v16.51.1',DESTINATION_APP='erpnext-catalog-pinned-recovery-test')
            with patch.dict(os.environ,environment), patch.object(job.subprocess,'run') as command:
                with self.assertRaisesRegex(RuntimeError,'cannot retry blindly'): job.run()
                command.assert_not_called()


if __name__=='__main__': unittest.main()
