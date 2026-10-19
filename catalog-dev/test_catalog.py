"""Local library render tests. No Docker daemon required; not official CI."""
import argparse
import ast
import copy
import sys
import unittest
from pathlib import Path
import yaml
from render_catalog import render

parser = argparse.ArgumentParser()
parser.add_argument('--apps-root', required=True, type=Path)
args, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0], *remaining]
APP = args.apps_root.resolve() / 'ix-dev/community/erpnext'


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.values = yaml.safe_load((APP / 'ix_values.yaml').read_text())
        self.values.update(yaml.safe_load((APP / 'templates/test_values/basic-values.yaml').read_text()))
        self.values['ix_context'] = {'app_name': 'erpnext-catalog-test', 'app_metadata': {'title': 'ERPNext', 'train': 'community'}}

    def test_native_render_and_dependencies(self):
        doc = render(self.values, args.apps_root)
        services = doc['services']
        self.assertEqual(len(services), 12)
        self.assertEqual([n for n, s in services.items() if s.get('ports')], ['frontend'])
        for name in ('backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler'):
            self.assertEqual(services[name]['depends_on']['initializer']['condition'], 'service_completed_successfully')
            self.assertEqual(services[name]['user'], '1000:1000')
        self.assertEqual(services['initializer']['depends_on']['bootstrap']['condition'], 'service_completed_successfully')
        self.assertEqual(services['db']['user'], '999:999')
        self.assertIn(0, services['frontend']['group_add'])
        self.assertEqual(services['permissions']['user'], '0:0')
        self.assertEqual(doc['x-portals'][0]['port'], 18084)
        self.assertEqual(services['frontend']['ports'][0]['target'], 8080)
        self.assertFalse(any(s.get('privileged') for s in services.values()))
        self.assertNotIn('/var/run/docker.sock', yaml.safe_dump(doc))
        self.assertIn('/persistent/sites', [v['target'] for v in services['bootstrap']['volumes']])

    def test_host_paths_and_dollar_password(self):
        self.values['erpnext']['db_password'] = 'example$database-password'
        for key in ('sites', 'logs', 'db_data', 'queue_data'):
            self.values['storage'][key] = {'type': 'host_path', 'host_path_config': {'path': '/mnt/labpool/catalog/' + key, 'auto_permissions': True}}
        doc = render(self.values, args.apps_root)
        self.assertEqual(doc['services']['db']['environment']['MARIADB_ROOT_PASSWORD'], 'example$$database-password')
        self.assertEqual(doc['services']['initializer']['environment']['DB_ROOT_PASSWORD'], 'example$$database-password')
        self.assertEqual(doc['services']['initializer']['volumes'][1]['type'], 'bind')
        for config in doc['configs'].values():
            ast.parse(config['content'].replace('$$', '$'))

    def test_bootstrap_blocks_unmanaged_or_changed_image(self):
        doc = render(self.values, args.apps_root)
        script = doc['configs']['catalog_bootstrap']['content']
        # Execute the actual rendered bootstrap against temp dirs by replacing only
        # the two hardcoded container paths. This checks fresh copy, repeat start,
        # and image-change refusal without Docker.
        import os, tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'image-sites'; source.mkdir()
            (source / 'assets').mkdir(); (source / 'assets/test.js').write_text('asset')
            destination = Path(tmp) / 'persistent'; destination.mkdir()
            patched = script.replace("Path('/persistent/sites')", 'Path(' + repr(str(destination)) + ')').replace("'/home/frappe/frappe-bench/sites'", repr(str(source)))
            # fcntl is available in Linux container/runtime. On Windows, skip just
            # this execution test; all render checks remain available.
            if os.name == 'nt': self.skipTest('Linux bootstrap execution')
            with patch.dict(os.environ, {'CATALOG_IMAGE': 'frappe/erpnext:v16.51.1'}):
                exec(compile(patched, '<bootstrap>', 'exec'), {})
                exec(compile(patched, '<bootstrap>', 'exec'), {})
            self.assertEqual((destination / 'assets/test.js').read_text(), 'asset')
            with patch.dict(os.environ, {'CATALOG_IMAGE': 'frappe/erpnext:v16.51.2'}):
                with self.assertRaises(SystemExit): exec(compile(patched, '<bootstrap>', 'exec'), {})

    def test_unmanaged_storage_refused(self):
        import os, tempfile
        if os.name == 'nt': self.skipTest('Linux bootstrap execution')
        from unittest.mock import patch
        script = render(self.values, args.apps_root)['configs']['catalog_bootstrap']['content']
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            (destination / 'unrelated').write_text('preserve')
            patched = script.replace("Path('/persistent/sites')", 'Path(' + repr(tmp) + ')')
            with patch.dict(os.environ, {'CATALOG_IMAGE': 'frappe/erpnext:v16.51.1'}):
                with self.assertRaises(SystemExit): exec(compile(patched, '<bootstrap>', 'exec'), {})
            self.assertEqual((destination / 'unrelated').read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main()
