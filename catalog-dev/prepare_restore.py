"""Prepare an independent catalog restore clone; never edit the source app."""
import argparse
import copy
from pathlib import Path, PurePosixPath
import secrets
import re
import uuid

import yaml
from render_catalog import render_legacy as render
from prepare_healthcheck_update import RUNTIME

APP_NAME = 'erpnext-catalog-restore-test'
LAB_APPS = (APP_NAME, 'erpnext-catalog-pinned-recovery-test', 'erpnext-catalog-interrupt-recovery-test', 'erpnext-catalog-patch-recovery-test')


def overlap(first, second):
    return first == second or first in second.parents or second in first.parents


def prepare(source, apps_root, lab_root, port=18085, app_name=APP_NAME):
    if len(app_name) > 40 or app_name not in LAB_APPS:
        raise ValueError('Dedicated lab restore app name required')
    destination = PurePosixPath(lab_root)
    if not destination.is_absolute() or not str(destination).startswith('/mnt/') or len(destination.parts) < 4 or '..' in destination.parts:
        raise ValueError('Dedicated destination below a VM pool required')
    services = source['services']
    paths = set()
    for service in services.values():
        for mount in service.get('volumes', []):
            if isinstance(mount, dict) and mount.get('type') == 'bind':
                paths.add(PurePosixPath(mount['source']))
    if any(overlap(destination, path) for path in paths):
        raise ValueError('Restore storage overlaps source storage')
    for mapping in services['frontend'].get('ports', []):
        if int(mapping['published']) == port:
            raise ValueError('Restore port must differ from source')
    if not 1024 <= port <= 65535:
        raise ValueError('Invalid port')
    site = services['frontend']['environment']['FRAPPE_SITE_NAME_HEADER']
    backup_operation = services['initializer']['environment']['EXPECTED_UPGRADE_OPERATION']
    if not re.fullmatch(r'[a-f0-9]{32}', backup_operation):
        raise ValueError('Invalid backup operation ID')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,120}', site) or '..' in site:
        raise ValueError('Invalid source site')
    source_sites = next(m['source'] for m in services['backend']['volumes']
        if isinstance(m, dict) and m.get('target') == '/home/frappe/frappe-bench/sites' and m['type'] == 'bind')
    app = apps_root.resolve() / 'ix-dev/community/erpnext'
    values = yaml.safe_load((app / 'ix_values.yaml').read_text())
    # Restore exact installed references even after catalog defaults gain pins.
    for key, service in (('image', 'backend'), ('mariadb_image', 'db'), ('redis_image', 'redis-cache')):
        reference = services[service]['image']
        default = values['images'][key]
        prefix = default['repository'] + ':' + default['tag'].split('@')[0]
        from patch_policy import SOURCE
        older_patch_source = key == 'image' and reference == SOURCE and app_name == 'erpnext-catalog-patch-recovery-test'
        if not older_patch_source and not re.fullmatch(re.escape(prefix) + r'(?:@sha256:[a-f0-9]{64})?', reference):
            raise ValueError('Source version differs from supported catalog version')
        values['images'][key]['tag'] = reference[len(default['repository']) + 1:]
    values.update(erpnext={'site_name': site, 'admin_password': secrets.token_urlsafe(24),
        'db_password': secrets.token_urlsafe(24)}, storage={}, labels=[],
        network={'web_port': {'bind_mode': 'published', 'port_number': port, 'host_ips': []}},
        resources={'limits': {'cpus': 2, 'memory': 2048}},
        ix_context={'app_name': app_name, 'app_metadata': {'title': 'ERPNext Restore Test', 'train': 'community'}})
    for name in ('sites', 'logs', 'db_data', 'queue_data'):
        values['storage'][name] = {'type': 'host_path', 'host_path_config': {
            'path': str(destination / name), 'auto_permissions': True, 'acl_enable': False}}
    initialize = render(values, apps_root)
    network_name = 'ix-' + app_name + '_default'
    if any(config.get('name') == network_name for config in source.get('networks', {}).values()):
        raise ValueError('Destination network overlaps source network')
    initialize['networks'] = {'default': {'name': network_name}}
    for name in (*RUNTIME, 'initializer', 'bootstrap', 'db', 'redis-cache', 'redis-queue'):
        if initialize['services'][name]['image'] != services[name]['image']:
            raise ValueError('Source and destination images must match exactly')
    operation = uuid.uuid4().hex
    restore = copy.deepcopy(initialize)
    restore['configs']['catalog_restore'] = {'content': Path(__file__).with_name('restore_job.py').read_text().replace('$', '$$')}
    restore['configs']['catalog_patch_policy'] = {'content': Path(__file__).with_name('patch_policy.py').read_text().replace('$', '$$')}
    restore['services'] = {name: copy.deepcopy(initialize['services'][name])
        for name in ('db', 'redis-cache', 'redis-queue', 'permissions')}
    job = {key: copy.deepcopy(value) for key, value in initialize['services']['backend'].items()
        if key in ('image', 'volumes', 'networks', 'user', 'group_add', 'deploy', 'security_opt', 'cap_drop')}
    job['volumes'].append({'type': 'bind', 'source': str(PurePosixPath(source_sites) / '.catalog-recovery' / backup_operation),
        'target': '/recovery', 'read_only': True, 'bind': {'create_host_path': False}})
    job.update(entrypoint=['/home/frappe/frappe-bench/env/bin/python', '/catalog/restore.py'],
        command=[], restart='no', healthcheck={'disable': True},
        environment={'SITE_NAME': site, 'CATALOG_IMAGE': services['backend']['image'],
            'DESTINATION_APP': app_name, 'BACKUP_OPERATION': backup_operation,
            'RESTORE_OPERATION': operation, 'DEST_DB_ROOT_PASSWORD': values['erpnext']['db_password']},
        configs=[{'source': 'catalog_restore', 'target': '/catalog/restore.py', 'mode': 292},
            {'source': 'catalog_patch_policy', 'target': '/catalog/patch_policy.py', 'mode': 292}],
        depends_on={name: {'condition': 'service_healthy'} for name in ('db', 'redis-cache', 'redis-queue')})
    job['depends_on']['permissions'] = {'condition': 'service_completed_successfully'}
    restore['services']['restore-job'] = job
    restore.pop('x-portals', None)
    resume = copy.deepcopy(initialize)
    resume['services']['initializer']['environment'].update(
        EXPECTED_UPGRADE_OPERATION=operation, EXPECTED_UPGRADE_IMAGE=services['backend']['image'])
    for name in RUNTIME:
        resume['services'][name]['environment']['EXPECTED_UPGRADE_OPERATION'] = operation
    return {'01-initialize-clone.yaml': initialize, '02-restore-clone.yaml': restore,
        '03-start-restored-clone.yaml': resume}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-config', type=Path, required=True)
    parser.add_argument('--apps-root', type=Path, required=True)
    parser.add_argument('--lab-root', required=True)
    parser.add_argument('--port', type=int, default=18085)
    parser.add_argument('--app-name', default=APP_NAME, choices=LAB_APPS)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    source = yaml.safe_load(args.source_config.read_text(encoding='utf-8'))
    documents = prepare(source, args.apps_root, args.lab_root, args.port, args.app_name)
    args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, document in documents.items():
        path = args.output_dir / name
        with path.open('x', encoding='utf-8') as output:
            output.write('# PRIVATE isolated restore test. Never use source storage as destination.\n')
            yaml.safe_dump(document, output, sort_keys=False)
        path.chmod(0o600)
    print('Prepared three private stages for NEW ' + args.app_name + '. Source unchanged.')


if __name__ == '__main__': main()
