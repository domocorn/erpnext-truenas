"""Interruption-plan isolation and pinned backup/retry guards."""
import copy
import os
import unittest
from unittest.mock import patch
import yaml
import test_rehearsal as rehearsal_tests
from prepare_interruption import prepare
from render_catalog import render_legacy as render


class InterruptionTests(rehearsal_tests.RehearsalTests):
    def test_hook_injection_requires_explicit_ack_and_migration_phase(self):
        import interruption_job
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'acknowledgement'):
                interruption_job.main()
            os.environ.update(INTERRUPTION_TEST_ACK='disposable-recovery-clone', UPGRADE_PHASE='backup')
            with self.assertRaisesRegex(RuntimeError, 'same-image migration'):
                interruption_job.main()

    def test_pinned_recovered_source_requires_expected_previous_state(self):
        image=self.image+'@sha256:'+'b'*64
        (self.root/'.catalog-image').write_text(image)
        os.environ.update(SOURCE_IMAGE=image,TARGET_IMAGE=image,PREVIOUS_UPGRADE_OPERATION='c'*32)
        with self.assertRaisesRegex(RuntimeError,'state is missing'):
            self.job.run_job()
        state=dict(layout='catalog-restore-v1',status='resumed',target=image,operation='d'*32)
        path=self.root/self.site/'.nas-upgrade-state.json'
        self.job.write_json(path,state)
        with self.assertRaisesRegex(RuntimeError,'unsupported operation'):
            self.job.run_job()
        state['operation']='c'*32
        self.job.write_json(path,state)
        with patch.object(self.job.subprocess,'run',self.command): self.job.run_job()
        self.assertEqual(self.state()['source'],image)
        self.assertEqual(self.state()['target'],image)

    def test_interruption_plan_preserves_source_and_has_explicit_ack(self):
        args=rehearsal_tests.args
        app=args.apps_root/'ix-dev/community/erpnext'
        values=yaml.safe_load((app/'ix_values.yaml').read_text())
        values.update(yaml.safe_load((app/'templates/test_values/basic-values.yaml').read_text()))
        values['ix_context']={'app_name':'erpnext-catalog-pinned-recovery-test','app_metadata':{'title':'ERPNext','train':'community'}}
        source=render(values,args.apps_root)
        source['networks']={'default':{'name':'ix-erpnext-catalog-pinned-recovery-test_default'}}
        source['services']['initializer']['environment']['EXPECTED_UPGRADE_OPERATION']='c'*32
        before=copy.deepcopy(source)
        documents=prepare(source)
        self.assertEqual(before,source)
        self.assertEqual(len(documents),4)
        job=documents['02-interrupt-migration.yaml']['services']['rehearsal-job']
        self.assertEqual(job['environment']['INTERRUPTION_TEST_ACK'],'disposable-recovery-clone')
        self.assertEqual(job['environment']['PREVIOUS_UPGRADE_OPERATION'],'c'*32)
        self.assertEqual(job['volumes'],source['services']['backend']['volumes'])
        for document in documents.values():
            for name in ('db','redis-cache','redis-queue','permissions'):
                self.assertEqual(document['services'][name],source['services'][name])
        source['networks']['default']['name']='original-source'
        with self.assertRaises(ValueError): prepare(source)


if __name__=='__main__': unittest.main()
