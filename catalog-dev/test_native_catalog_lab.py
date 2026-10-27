"""Ownership and recovery checks for a root-run single-app lab catalog overlay."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import native_catalog_lab as lab


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = self.root/'catalog'
        (self.catalog/'trains/community').mkdir(parents=True)
        self.state = self.root/'state'
        self.state.mkdir()
        self.bundle = self.root/'bundle'
        self.original = {'community': {'unrelated-app': {'latest_version': '8.0.0'}}}
        (self.catalog/'catalog.json').write_text(json.dumps(self.original))
        entries, files = {}, {}
        for role, version in [('source', '0.9.0'), ('target', '1.0.0')]:
            app = self.bundle/role/'trains/community'/lab.APP
            app.mkdir(parents=True)
            (app/'app.yaml').write_text(version)
            entries[role] = {'healthy': True, 'latest_version': version}
            files[role] = lab.tree_hash(app)
            (self.bundle/role/'catalog.json').write_text(json.dumps({'community': {lab.APP: entries[role]}}))
        (self.bundle/'manifest.json').write_text(json.dumps({'entries': entries, 'app_files': files}))
        self.entries = entries
        for name, value in [('CATALOG', self.catalog), ('STATE', self.state)]:
            patcher = patch.object(lab, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name in ('refresh', 'validate_catalog'):
            patcher = patch.object(lab, name)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.call = patch.object(lab, 'call', return_value=[{'custom_app': False, 'version': '0.9.0',
            'state': 'RUNNING', 'metadata': {'name': lab.APP}}]).start()
        self.addCleanup(patch.stopall)

    def index(self):
        return json.loads((self.catalog/'catalog.json').read_text())

    def test_stage_update_remove_preserves_unrelated_changes(self):
        lab.stage(self.bundle, 'source')
        catalog = self.index()
        catalog['community']['unrelated-app']['latest_version'] = '9.0.0'
        (self.catalog/'catalog.json').write_text(json.dumps(catalog))
        lab.stage(self.bundle, 'target')
        self.assertEqual(self.index()['community'][lab.APP], self.entries['target'])
        self.assertTrue((self.catalog/'trains/community'/('.'+lab.APP+'-source-preserved')).is_dir())
        lab.remove()
        self.assertNotIn(lab.APP, self.index()['community'])
        self.assertEqual(self.index()['community']['unrelated-app']['latest_version'], '9.0.0')
        self.assertEqual(json.loads((self.state/'original-catalog.json').read_text()), self.original)

    def test_refuses_foreign_entry_and_modified_live_files(self):
        original = self.index()
        foreign = copy.deepcopy(original)
        foreign['community'][lab.APP] = {'foreign': True}
        (self.catalog/'catalog.json').write_text(json.dumps(foreign))
        with self.assertRaises(RuntimeError):
            lab.stage(self.bundle, 'source')
        self.assertEqual(self.index(), foreign)
        (self.catalog/'catalog.json').write_text(json.dumps(original))
        lab.stage(self.bundle, 'source')
        (self.catalog/'trains/community'/lab.APP/'app.yaml').write_text('externally modified')
        with self.assertRaises(RuntimeError):
            lab.stage(self.bundle, 'target')
        with self.assertRaises(RuntimeError):
            lab.remove()
        self.assertEqual(self.index()['community'][lab.APP], self.entries['source'])

    def test_tampered_bundle_and_symlink_are_rejected(self):
        app = self.bundle/'source/trains/community'/lab.APP
        (app/'app.yaml').write_text('tampered')
        with self.assertRaises(RuntimeError):
            lab.stage(self.bundle, 'source')
        self.assertEqual(self.index(), self.original)
        (app/'link').symlink_to('/etc/passwd')
        with self.assertRaises(RuntimeError):
            lab.tree_hash(app)

    def test_pending_journal_can_remove_owned_partial_stage(self):
        lab.stage(self.bundle, 'source')
        original_atomic = lab.atomic
        def fail_index(path, content, mode=0o600):
            if path == self.catalog/'catalog.json':
                raise OSError('simulated index write failure')
            return original_atomic(path, content, mode)
        with patch.object(lab, 'atomic', side_effect=fail_index):
            with self.assertRaises(OSError):
                lab.stage(self.bundle, 'target')
        self.assertTrue(json.loads((self.state/'state.json').read_text())['pending'])
        with self.assertRaises(RuntimeError):
            lab.stage(self.bundle, 'target')
        lab.remove()
        self.assertEqual(self.index(), self.original)


if __name__ == '__main__':
    unittest.main()
