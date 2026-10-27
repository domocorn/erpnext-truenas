"""One-deployment lifecycle sequencing, lifetime exclusion and failure guards."""
import copy
import fcntl
import json
import os
import subprocess
import unittest
from unittest.mock import Mock, patch
import yaml
import test_rehearsal as rehearsal_tests
from coordinator import coordinate
from prepare_coordinator import prepare
from render_catalog import render_legacy as render


class CoordinatorTests(rehearsal_tests.RehearsalTests):
    def test_sequence_lifetime_lock_and_idempotent_repeat(self):
        events=[]
        def command(arguments,**kwargs):
            events.append('backup' if 'backup' in arguments else 'migrate')
            self.command(arguments,**kwargs)
        def initialize():
            events.append('initialize')
            self.assertEqual(self.state()['status'],'migrated' if events.count('initialize')==1 else 'resumed')
            with (self.root/'.catalog-runtime.lock').open('a') as contender:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(contender,fcntl.LOCK_SH|fcntl.LOCK_NB)
        with patch.object(self.job.subprocess,'run',command):
            coordinate(self.job,initialize)
            coordinate(self.job,initialize)
        self.assertEqual(events,['backup','migrate','initialize','initialize'])
        self.assertEqual(self.state()['status'],'resumed')
        config=json.loads((self.root/self.site/'site_config.json').read_text())
        self.assertEqual(config['maintenance_mode'],0)
        self.assertEqual(config['pause_scheduler'],1)

    def test_failed_migration_never_initializes_or_retries(self):
        def command(arguments,**kwargs):
            if 'migrate' in arguments: raise subprocess.CalledProcessError(1,'bench')
            self.command(arguments,**kwargs)
        initialize=Mock()
        with patch.object(self.job.subprocess,'run',command):
            with self.assertRaises(subprocess.CalledProcessError): coordinate(self.job,initialize)
            self.assertEqual(self.state()['status'],'migrating')
            with self.assertRaises(RuntimeError): coordinate(self.job,initialize)
        initialize.assert_not_called()

    def test_resume_failure_can_repeat_without_remigrating(self):
        with patch.object(self.job.subprocess,'run',self.command):
            with self.assertRaisesRegex(RuntimeError,'resume failure'):
                coordinate(self.job,Mock(side_effect=RuntimeError('resume failure')))
            self.assertEqual(self.state()['status'],'migrated')
            coordinate(self.job,lambda:None)
        self.assertEqual(self.state()['status'],'resumed')
        self.assertEqual(sum('migrate' in call for call in self.calls),1)

    def test_active_runtime_blocks_before_mutation(self):
        with (self.root/'.catalog-runtime.lock').open('a') as runtime:
            fcntl.flock(runtime,fcntl.LOCK_SH|fcntl.LOCK_NB)
            with patch.object(self.job.subprocess,'run') as command:
                with self.assertRaises(BlockingIOError): coordinate(self.job,Mock())
                command.assert_not_called()
        self.assertFalse((self.root/self.site/'.nas-upgrade-state.json').exists())

    def test_plan_preserves_images_storage_secrets_and_runtime_dependencies(self):
        args=rehearsal_tests.args
        app=args.apps_root/'ix-dev/community/erpnext'
        values=yaml.safe_load((app/'ix_values.yaml').read_text())
        values.update(yaml.safe_load((app/'templates/test_values/basic-values.yaml').read_text()))
        values['ix_context']={'app_name':'erpnext-catalog-interrupt-recovery-test','app_metadata':{'title':'ERPNext','train':'community'}}
        source=render(values,args.apps_root)
        source['networks']={'default':{'name':'ix-erpnext-catalog-interrupt-recovery-test_default'}}
        source['services']['initializer']['environment']['EXPECTED_UPGRADE_OPERATION']='c'*32
        before=copy.deepcopy(source)
        result=prepare(source)
        self.assertEqual(source,before)
        for name,service in source['services'].items():
            for key in ('image','volumes','ports','networks'):
                self.assertEqual(result['services'][name].get(key),service.get(key))
        self.assertEqual(result['services']['initializer']['environment']['DB_ROOT_PASSWORD'],source['services']['initializer']['environment']['DB_ROOT_PASSWORD'])
        self.assertEqual(result['services']['backend']['depends_on']['initializer']['condition'],'service_completed_successfully')
        source['networks']['default']['name']='original-source'
        with self.assertRaises(ValueError): prepare(source)


if __name__=='__main__': unittest.main()
