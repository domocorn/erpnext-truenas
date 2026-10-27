"""Read-only queue checks and refusal before backup/migration state changes."""
import os
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import test_rehearsal as rehearsal_tests
from queue_guard import check_queues


class QueueGuardTests(rehearsal_tests.RehearsalTests):
    def test_empty_queue_and_registries_pass_without_cleanup(self):
        registry=SimpleNamespace(get_job_ids=Mock(return_value=[]))
        factory=Mock(return_value=registry)
        check_queues([SimpleNamespace(name='short',count=0,connection=object())],[factory])
        registry.get_job_ids.assert_called_once_with(cleanup=False)

    def test_pending_or_unresolved_work_blocks(self):
        factory=Mock(return_value=SimpleNamespace(get_job_ids=Mock(return_value=['job'])))
        with self.assertRaisesRegex(RuntimeError,'Queued work'):
            check_queues([SimpleNamespace(name='short',count=1,connection=None)],[factory])
        factory.assert_not_called()
        with self.assertRaisesRegex(RuntimeError,'Unresolved'):
            check_queues([SimpleNamespace(name='short',count=0,connection=None)],[factory])

    def test_queue_failure_precedes_new_backup_and_migration_mutation(self):
        with patch.object(self.job,'assert_queue_quiescent',side_effect=RuntimeError('queue not empty')):
            with self.assertRaisesRegex(RuntimeError,'queue not empty'): self.job.run_job()
        self.assertFalse((self.root/self.site/'.nas-upgrade-state.json').exists())
        with patch.object(self.job.subprocess,'run',self.command): self.job.run_job()
        os.environ['UPGRADE_PHASE']='migrate'
        with patch.object(self.job,'assert_queue_quiescent',side_effect=RuntimeError('queue not empty')):
            with self.assertRaisesRegex(RuntimeError,'queue not empty'): self.job.run_job()
        self.assertEqual(self.state()['status'],'backed_up')

    def test_update_preserves_deployment_and_operation_and_is_idempotent(self):
        import yaml
        from render_catalog import render_legacy as render
        from patch_policy import SOURCE
        from prepare_patch import prepare as patch_plan
        from prepare_worker_shutdown import prepare
        args=rehearsal_tests.args
        app=args.apps_root/'ix-dev/community/erpnext'
        values=yaml.safe_load((app/'ix_values.yaml').read_text())
        values['images']['image']['tag']=SOURCE.split(':',1)[1]
        values.update(yaml.safe_load((app/'templates/test_values/basic-values.yaml').read_text()))
        values['ix_context']={'app_name':'erpnext-catalog-patch-test','app_metadata':{'title':'ERPNext','train':'community'}}
        source=render(values,args.apps_root)
        source['networks']={'default':{'name':'ix-erpnext-catalog-patch-test_default'}}
        source=patch_plan(source)
        before=copy.deepcopy(source)
        result=prepare(source,args.apps_root)
        self.assertEqual(source,before)
        self.assertEqual(result,prepare(result,args.apps_root))
        for name,service in source['services'].items():
            for key in ('image','volumes','ports','networks'):
                self.assertEqual(result['services'][name].get(key),service.get(key))
        self.assertEqual(result['services']['initializer']['environment'],source['services']['initializer']['environment'])
        self.assertEqual(result['services']['db'],source['services']['db'])
        for name in ('queue-short','queue-long'):
            self.assertEqual(result['services'][name]['stop_grace_period'],'120s')


if __name__=='__main__': unittest.main()
