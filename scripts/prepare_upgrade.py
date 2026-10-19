"""Generate staged PRIVATE YAML from the exact installed configuration."""
import argparse
import copy
from pathlib import Path
import re
import uuid
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = {'backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler'}


def version(image):
    match = re.fullmatch(r'frappe/erpnext:v(\d+)\.(\d+)\.(\d+)', image)
    if not match:
        raise ValueError('Only pinned official ERPNext vMAJOR.MINOR.PATCH images are supported')
    return tuple(map(int, match.groups()))


def prepare(original, target, rehearsal=False, operation=None):
    services = original['services']
    if not RUNTIME.issubset(services) or 'initializer' not in services:
        raise ValueError('Expected the project prototype service layout')
    source = services['backend']['image']
    old, new = version(source), version(target)
    if new[0] != old[0] or new < old or (new == old and not rehearsal):
        raise ValueError('Same-major upgrade only. Equal versions require --rehearsal; downgrade forbidden.')
    if any(s.get('image') != source for s in services.values() if s.get('image', '').startswith('frappe/erpnext:')):
        raise ValueError('Source ERPNext service versions are inconsistent')
    site = services['frontend']['environment']['FRAPPE_SITE_NAME_HEADER']
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,120}', site) or '..' in site:
        raise ValueError('Invalid site name')
    operation = operation or uuid.uuid4().hex
    if not re.fullmatch('[a-f0-9]{32}', operation):
        raise ValueError('Invalid operation ID')
    script = (ROOT / 'scripts/upgrade_job.py').read_text().replace('$', '$$')
    base = {k: copy.deepcopy(v) for k, v in original.items() if k in ('volumes', 'networks')}
    outputs = {}
    for filename, phase, image, failure in (
            ('01-backup.yaml', 'backup', source, False),
            ('02-migrate.yaml', 'migrate', target, False),
            ('02-test-failure.yaml', 'migrate', target, True)):
        doc = copy.deepcopy(base)
        doc['services'] = {n: copy.deepcopy(services[n]) for n in ('db', 'redis-cache', 'redis-queue')}
        job = {k: copy.deepcopy(v) for k, v in services['backend'].items() if k in ('volumes', 'networks', 'platform', 'user', 'working_dir')}
        job.update(image=image, restart='no',
                   entrypoint=['/home/frappe/frappe-bench/env/bin/python', '-c'], command=[script],
                   environment={'SITE_NAME': site, 'OPERATION_ID': operation, 'TARGET_IMAGE': target,
                                'SOURCE_IMAGE': source, 'UPGRADE_PHASE': phase, 'SIMULATE_FAILURE': '1' if failure else '0'},
                   depends_on={n: {'condition': 'service_healthy'} for n in ('db', 'redis-cache', 'redis-queue')})
        doc['services']['upgrade-job'] = job
        outputs[filename] = doc
    resume = copy.deepcopy(original)
    # Do not introduce another project name; edit the SAME existing TrueNAS app.
    resume.pop('name', None)
    resume.pop('x-erpnext-image', None)
    for service in resume['services'].values():
        if service.get('image', '').startswith('frappe/erpnext:'):
            service['image'] = target
    initializer = resume['services']['initializer']
    initializer['command'] = [(ROOT / 'scripts/initialize.py').read_text().replace('$', '$$')]
    initializer['environment']['EXPECTED_UPGRADE_OPERATION'] = operation
    initializer['environment']['EXPECTED_UPGRADE_IMAGE'] = target
    outputs['03-resume.yaml'] = resume
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-config', required=True, type=Path)
    parser.add_argument('--target', required=True, help='Pinned tag, e.g. v16.51.1')
    parser.add_argument('--rehearsal', action='store_true')
    parser.add_argument('--numbered-stages', action='store_true', help='Use distinct 01–05 filenames, including blocked-resume test')
    parser.add_argument('--output-dir', type=Path, default=Path('generated/upgrade'))
    args = parser.parse_args()
    source = yaml.safe_load(args.from_config.read_text())
    target = 'frappe/erpnext:' + args.target
    outputs = prepare(source, target, args.rehearsal)
    if args.numbered_stages:
        outputs = numbered_stages(outputs)
    # Never silently overwrite the operation IDs for an in-progress run.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for name, doc in outputs.items():
        path = args.output_dir / name
        path.write_text('# PRIVATE: credentials included. TEST VM ONLY.\n' + yaml.safe_dump(doc, sort_keys=False))
        path.chmod(0o600)
    print('Created backup, migration, deliberate failure, and guarded resume configurations.')
    print('Read docs/UPGRADE-TEST.md before applying. Stop the existing test app first.')


def numbered_stages(outputs):
    return {
        '01-backup.yaml': outputs['01-backup.yaml'],
        '02-simulated-failure.yaml': outputs['02-test-failure.yaml'],
        '03-verify-startup-blocked.yaml': copy.deepcopy(outputs['03-resume.yaml']),
        '04-migrate.yaml': outputs['02-migrate.yaml'],
        '05-resume.yaml': outputs['03-resume.yaml'],
    }


if __name__ == '__main__':
    main()
