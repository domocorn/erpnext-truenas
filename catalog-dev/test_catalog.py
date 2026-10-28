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
        expected_image = 'frappe/erpnext:' + self.values['images']['image']['tag']
        self.assertIn('@sha256:', expected_image)
        from patch_policy import SOURCE, TARGET, SOURCE_VERSION, TARGET_VERSION, validate_patch, SOURCE_DIGEST, SOURCE_ID
        self.assertEqual(expected_image, TARGET)
        self.assertEqual(self.values['images']['previous_image']['repository'] + ':' + self.values['images']['previous_image']['tag'], SOURCE)
        metadata = yaml.safe_load((APP / 'app.yaml').read_text())
        self.assertEqual(metadata['app_version'], TARGET_VERSION)
        self.assertNotEqual(SOURCE_VERSION, TARGET_VERSION)
        policy = next(config['content'] for config in doc['configs'].values() if 'def validate_patch(' in config['content'])
        namespace = {}
        exec(compile(policy, '<rendered-patch-policy>', 'exec'), namespace)
        namespace['validate_patch'](SOURCE, TARGET, SOURCE_DIGEST, SOURCE_ID)
        with self.assertRaises(RuntimeError):
            namespace['validate_patch'](TARGET, SOURCE, SOURCE_DIGEST, SOURCE_ID)
        for name in ('bootstrap', 'initializer', 'backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler'):
            self.assertEqual(services[name]['image'], expected_image)
            if name != 'initializer':
                self.assertEqual(services[name]['environment']['CATALOG_IMAGE'], expected_image)
        self.assertEqual(len(services), 13)
        self.assertEqual(services['upgrade-backup']['image'], self.values['images']['previous_image']['repository']+':'+self.values['images']['previous_image']['tag'])
        self.assertEqual(services['initializer']['depends_on']['upgrade-backup']['condition'],'service_completed_successfully')
        self.assertEqual(services['bootstrap']['command'],['bootstrap'])
        self.assertEqual(services['initializer']['command'],['initialize'])
        self.assertNotIn('CATALOG_NATIVE_FAILURE_ACK',yaml.safe_dump(doc))
        self.assertEqual([n for n, s in services.items() if s.get('ports')], ['frontend'])
        for name in ('backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler'):
            self.assertEqual(services[name]['depends_on']['initializer']['condition'], 'service_completed_successfully')
            self.assertEqual(services[name]['user'], '1000:1000')
        self.assertEqual(services['initializer']['depends_on']['bootstrap']['condition'], 'service_completed_successfully')
        self.assertEqual(services['db']['user'], '999:999')
        self.assertIn(0, services['frontend']['group_add'])
        self.assertEqual(services['permissions']['user'], '0:0')
        for name in ('queue-short','queue-long'):
            self.assertEqual(services[name]['stop_grace_period'],'120s')
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

    def health_namespace(self):
        doc = render(self.values, args.apps_root)
        namespace = {'__name__': 'health_test'}
        exec(compile(doc['configs']['catalog_health']['content'].replace('$$', '$'), '<health>', 'exec'), namespace)
        return namespace

    def test_runtime_gate_rejects_incomplete_or_mismatched_upgrade(self):
        import json, os, tempfile
        from types import SimpleNamespace
        from unittest.mock import patch
        script = render(self.values, args.apps_root)['configs']['catalog_runtime']['content'].replace('$$', '$')
        namespace = {'__name__': 'runtime_test'}
        with patch.dict(sys.modules, {'fcntl': SimpleNamespace()} if os.name == 'nt' else {}):
            exec(compile(script, '<runtime>', 'exec'), namespace)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = 'test.local'
            image = 'frappe/erpnext:v16.51.1'
            (root / '.catalog-site-name').write_text(site)
            (root / '.catalog-image').write_text(image)
            folder = root / site
            folder.mkdir()
            with self.assertRaises(RuntimeError):
                namespace['validate_state'](root, site, image)
            (folder / '.nas-initialized').touch()
            namespace['validate_state'](root, site, image)
            with self.assertRaises(RuntimeError):
                namespace['validate_state'](root, site, image + '-different')
            state = {'operation': 'test-operation', 'target': image}
            for status in ('backing_up', 'backed_up', 'migrating', 'migrated', 'failed'):
                state['status'] = status
                (folder / '.nas-upgrade-state.json').write_text(json.dumps(state))
                with self.assertRaises(RuntimeError):
                    namespace['validate_state'](root, site, image, 'test-operation')
            state['status'] = 'resumed'
            (folder / '.nas-upgrade-state.json').write_text(json.dumps(state))
            namespace['validate_state'](root, site, image, 'test-operation')
            with self.assertRaises(RuntimeError):
                namespace['validate_state'](root, site, image, 'wrong-operation')

    def test_runtime_lock_lifetime_and_signal_forwarding(self):
        import os, select, signal, subprocess, tempfile
        if os.name == 'nt':
            self.skipTest('Linux runtime lock and process group execution')
        import fcntl
        script = render(self.values, args.apps_root)['configs']['catalog_runtime']['content'].replace('$$', '$')
        with tempfile.TemporaryDirectory() as tmp:
            bench = Path(tmp)
            root = bench / 'sites'
            root.mkdir()
            site = 'test.local'
            (root / site).mkdir()
            (root / site / '.nas-initialized').touch()
            (root / '.catalog-site-name').write_text(site)
            (root / '.catalog-image').write_text('test-image')
            script = script.replace("BENCH = Path('/home/frappe/frappe-bench')", 'BENCH = Path(' + repr(tmp) + ')')
            script = script.replace("IMAGE_ENTRYPOINT = ['/usr/local/bin/entrypoint.sh']", 'IMAGE_ENTRYPOINT = []')
            path = bench / 'runtime.py'
            path.write_text(script)
            env = dict(os.environ, SITE_NAME=site, CATALOG_IMAGE='test-image')
            child = 'import signal,time,sys; signal.signal(signal.SIGTERM,lambda *a: sys.exit(0)); print("READY",flush=True); time.sleep(60)'
            command = [sys.executable, str(path), sys.executable, '-c', child]
            processes = []
            try:
                for _ in range(2):
                    process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    processes.append(process)
                    self.assertTrue(select.select([process.stdout], [], [], 10)[0], 'Child did not start')
                    self.assertEqual(process.stdout.readline().strip(), 'READY')
                with (root / '.catalog-runtime.lock').open('a') as lock:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    processes[0].send_signal(signal.SIGTERM)
                    self.assertEqual(processes[0].wait(timeout=10), 0)
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    processes[1].send_signal(signal.SIGTERM)
                    self.assertEqual(processes[1].wait(timeout=10), 0)
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    blocked = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
                    self.assertNotEqual(blocked.returncode, 0)
                    self.assertNotIn('READY', blocked.stdout)
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=10)
                    process.stdout.close()
                    process.stderr.close()

    def test_health_update_preserves_existing_deployment_and_refuses_image_change(self):
        from prepare_healthcheck_update import prepare_update, RUNTIME
        original = render(self.values, args.apps_root)
        original['services']['db']['environment']['MARIADB_ROOT_PASSWORD'] = 'retain$$existing-password'
        original['services']['frontend']['environment']['FRAPPE_SITE_NAME_HEADER'] = 'existing.example'
        updated = prepare_update(original, args.apps_root)
        self.assertEqual(updated, prepare_update(updated, args.apps_root))
        for name in RUNTIME:
            self.assertEqual(updated['services'][name]['environment']['SITE_NAME'], 'existing.example')
            # Remove exactly the permitted health-related changes and compare all else.
            for key in ('healthcheck', 'configs', 'environment'):
                if key in original['services'][name]:
                    updated['services'][name][key] = copy.deepcopy(original['services'][name][key])
                else:
                    updated['services'][name].pop(key, None)
        updated['configs'] = copy.deepcopy(original['configs'])
        self.assertEqual(updated, original)
        original['services']['backend']['image'] = 'frappe/erpnext:v16.51.2'
        with self.assertRaises(ValueError):
            prepare_update(original, args.apps_root)

    def test_runtime_update_is_idempotent_and_preserves_data_services(self):
        from prepare_runtime_update import prepare_runtime_update
        original = render(self.values, args.apps_root)
        original['services']['backend'].pop('entrypoint')
        original['services']['backend'].pop('command')
        updated = prepare_runtime_update(original, args.apps_root)
        self.assertEqual(updated, prepare_runtime_update(updated, args.apps_root))
        for name in ('db', 'redis-cache', 'redis-queue', 'initializer', 'bootstrap', 'permissions'):
            self.assertEqual(updated['services'][name], original['services'][name])
        for name in ('backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler'):
            for key in ('image', 'volumes', 'user', 'depends_on'):
                self.assertEqual(updated['services'][name].get(key), original['services'][name].get(key))
        self.assertEqual(updated['services']['backend']['command'], ['start.sh'])
        original['services']['backend']['entrypoint'] = ['custom-wrapper']
        with self.assertRaises(ValueError):
            prepare_runtime_update(original, args.apps_root)

    def test_runtime_health_and_http_failure(self):
        import io
        from unittest.mock import patch
        doc = render(self.values, args.apps_root)
        for name in ('frontend', 'backend', 'websocket', 'queue-short', 'queue-long', 'scheduler'):
            check = doc['services'][name]['healthcheck']
            self.assertEqual(check['test'][-1], name)
            self.assertFalse(check.get('disable', False))
        namespace = self.health_namespace()
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'{"message":"pong"}')) as request:
            namespace['check_http']('frontend', 'erpnext.localhost')
            self.assertEqual(request.call_args.args[0].get_header('Host'), 'erpnext.localhost')
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'{"message":"wrong"}')):
            with self.assertRaises(RuntimeError):
                namespace['check_http']('backend', 'erpnext.localhost')
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'0{"sid":"test"}')):
            namespace['check_http']('websocket', 'erpnext.localhost')

    def test_worker_requires_local_recent_heartbeat_and_correct_queues(self):
        import datetime
        import socket
        from types import SimpleNamespace
        from unittest.mock import patch
        namespace = self.health_namespace()
        worker = SimpleNamespace(hostname=socket.gethostname(),
            last_heartbeat=datetime.datetime.now(datetime.timezone.utc),
            queue_names=lambda: ['bench:short', 'bench:default'])
        modules = {'rq': SimpleNamespace(Worker=SimpleNamespace(all=lambda **kwargs: [worker])),
            'rq.defaults': SimpleNamespace(DEFAULT_WORKER_TTL=420),
            'frappe': SimpleNamespace(), 'frappe.utils': SimpleNamespace(),
            'frappe.utils.background_jobs': SimpleNamespace(get_queue=lambda q: SimpleNamespace(name='bench:' + q))}
        with patch.dict(sys.modules, modules):
            namespace['check_worker'](object(), ['short', 'default'])
            with self.assertRaises(RuntimeError):
                namespace['check_worker'](object(), ['long'])
            worker.last_heartbeat -= datetime.timedelta(seconds=400)
            namespace['check_worker'](object(), ['short', 'default'])
            worker.last_heartbeat -= datetime.timedelta(seconds=81)
            with self.assertRaises(RuntimeError):
                namespace['check_worker'](object(), ['short', 'default'])
            worker.last_heartbeat = datetime.datetime.now(datetime.timezone.utc)
            worker.hostname = 'another-container'
            with self.assertRaises(RuntimeError):
                namespace['check_worker'](object(), ['short', 'default'])

    def test_background_dependency_failure_and_scheduler_lock(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        namespace = self.health_namespace()
        frappe = SimpleNamespace(init=Mock(), connect=Mock(), destroy=Mock(),
            db=SimpleNamespace(sql=Mock()), cache=SimpleNamespace(ping=lambda: True))
        queue = SimpleNamespace(ping=lambda: True)
        modules = {'frappe': frappe, 'frappe.utils': SimpleNamespace(),
            'frappe.utils.background_jobs': SimpleNamespace(get_redis_conn=lambda: queue),
            'frappe.utils.scheduler': SimpleNamespace(is_schduler_process_running=lambda: False)}
        with patch.dict(sys.modules, modules), patch('os.chdir'):
            with self.assertRaises(RuntimeError):
                namespace['check_background']('scheduler', 'test.local')
            frappe.destroy.assert_called_once()
            frappe.destroy.reset_mock()
            frappe.db.sql.side_effect = ConnectionError('unavailable')
            with self.assertRaises(ConnectionError):
                namespace['check_background']('scheduler', 'test.local')
            frappe.destroy.assert_called_once()

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
