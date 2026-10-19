"""Generate offline catalog SAME-IMAGE backup/migration rehearsal stages."""
import argparse
import copy
from pathlib import Path
import re
import uuid

import yaml
from prepare_healthcheck_update import RUNTIME

ROOT = Path(__file__).resolve().parent
RESUME_SCRIPT = '''import fcntl
import os
import runpy
from pathlib import Path

functions = runpy.run_path('/catalog/rehearsal.py')
root = functions['ROOT']
with (root / '.catalog-runtime.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    site, operation, image = functions['identities']()
    import json
    state = json.loads((root / site / '.nas-upgrade-state.json').read_text())
    if not functions['matching_state'](state, operation, image) or state.get('status') not in ('migrated', 'resumed'):
        raise RuntimeError('Successful matching migration required; resume blocked')
    functions['verify_backup'](state)
    runpy.run_path('/catalog/initialize.py', run_name='__main__')
'''


def prepare(original, operation=None):
    operation = operation or uuid.uuid4().hex
    if not re.fullmatch(r'[a-f0-9]{32}', operation):
        raise ValueError('Invalid operation ID')
    services = original['services']
    image = services['backend']['image']
    if not re.fullmatch(r'frappe/erpnext:v16\.\d+\.\d+', image):
        raise ValueError('Pinned ERPNext v16 image required; digest transition not implemented')
    guard = original.get('configs', {}).get('catalog_runtime', {}).get('content', '')
    if '.catalog-runtime.lock' not in guard or 'LOCK_SH' not in guard:
        raise ValueError('Install and verify the runtime-guard revision first')
    for name in RUNTIME:
        service = services[name]
        if service['image'] != image or service.get('entrypoint') != [
                '/home/frappe/frappe-bench/env/bin/python', '/catalog/runtime.py']:
            raise ValueError('All runtime services must use the tested same-image guard')
        if service.get('environment', {}).get('CATALOG_IMAGE') != image:
            raise ValueError('Runtime image identity mismatch')
        if not any(isinstance(m, dict) and m.get('source') == 'catalog_runtime'
                and m.get('target') == '/catalog/runtime.py' for m in service.get('configs', [])):
            raise ValueError('Runtime guard config mount missing')
    site = services['frontend']['environment']['FRAPPE_SITE_NAME_HEADER']
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,120}', site) or '..' in site:
        raise ValueError('Invalid site name')
    if any(services[name]['image'] != image for name in ('initializer', 'bootstrap')):
        raise ValueError('Initialization image differs from runtime')
    if services['bootstrap'].get('environment', {}).get('CATALOG_IMAGE') != image:
        raise ValueError('Bootstrap image identity mismatch')
    if any(services[name].get('environment', {}).get('SITE_NAME') != site for name in RUNTIME):
        raise ValueError('Runtime site identities are inconsistent')
    base = copy.deepcopy(original)
    base['configs']['catalog_rehearsal'] = {
        'content': (ROOT / 'rehearsal_job.py').read_text(encoding='utf-8').replace('$', '$$')}
    environment = {'SITE_NAME': site, 'OPERATION_ID': operation,
        'SOURCE_IMAGE': image, 'TARGET_IMAGE': image}
    outputs = {}
    for filename, phase, failure in (
            ('01-backup.yaml', 'backup', '0'),
            ('02-simulated-failure.yaml', 'migrate', '1'),
            ('04-migrate.yaml', 'migrate', '0')):
        document = copy.deepcopy(base)
        document['services'] = {name: copy.deepcopy(services[name])
            for name in ('db', 'redis-cache', 'redis-queue', 'permissions') if name in services}
        job = {key: copy.deepcopy(value) for key, value in services['backend'].items()
            if key in ('image', 'volumes', 'networks', 'platform', 'user', 'group_add', 'deploy', 'security_opt', 'cap_drop')}
        job.update(restart='no', entrypoint=['/home/frappe/frappe-bench/env/bin/python', '/catalog/rehearsal.py'],
            command=[], healthcheck={'disable': True},
            environment=dict(environment, UPGRADE_PHASE=phase, SIMULATE_FAILURE=failure),
            configs=[{'source': 'catalog_rehearsal', 'target': '/catalog/rehearsal.py', 'mode': 292}],
            depends_on={name: {'condition': 'service_healthy'} for name in ('db', 'redis-cache', 'redis-queue')})
        if 'permissions' in document['services']:
            job['depends_on']['permissions'] = {'condition': 'service_completed_successfully'}
        document['services']['rehearsal-job'] = job
        document.pop('x-portals', None)
        outputs[filename] = document
    resume = copy.deepcopy(base)
    resume['configs']['catalog_rehearsal_resume'] = {'content': RESUME_SCRIPT}
    initializer = resume['services']['initializer']
    initializer['entrypoint'] = ['/home/frappe/frappe-bench/env/bin/python', '/catalog/rehearsal-resume.py']
    initializer['command'] = []
    initializer['environment'].update(environment,
        EXPECTED_UPGRADE_OPERATION=operation, EXPECTED_UPGRADE_IMAGE=image)
    mounts = initializer['configs']
    mounts[:] = [m for m in mounts if m.get('source') not in ('catalog_rehearsal', 'catalog_rehearsal_resume')]
    mounts.extend([{'source': 'catalog_rehearsal', 'target': '/catalog/rehearsal.py', 'mode': 292},
        {'source': 'catalog_rehearsal_resume', 'target': '/catalog/rehearsal-resume.py', 'mode': 292}])
    for name in RUNTIME:
        resume['services'][name]['environment']['EXPECTED_UPGRADE_OPERATION'] = operation
    outputs['03-verify-startup-blocked.yaml'] = copy.deepcopy(resume)
    outputs['05-resume.yaml'] = resume
    return dict(sorted(outputs.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed-yaml', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--rehearsal', action='store_true', required=True)
    args = parser.parse_args()
    documents = prepare(yaml.safe_load(args.installed_yaml.read_text(encoding='utf-8')))
    args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, document in documents.items():
        path = args.output_dir / name
        with path.open('x', encoding='utf-8') as output:
            output.write('# PRIVATE SAME-IMAGE rehearsal. TEST VM ONLY.\n')
            yaml.safe_dump(document, output, sort_keys=False)
        path.chmod(0o600)
    print('Created five private same-image rehearsal stages. Nothing deployed.')


if __name__ == '__main__':
    main()
