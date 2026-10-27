"""Prepare a same-content tag-to-digest transition on the disposable restored clone."""
import argparse
from pathlib import Path
import re
import uuid

import yaml
from prepare_healthcheck_update import RUNTIME
from prepare_rehearsal import prepare as rehearsal

ROOT = Path(__file__).resolve().parent


def prepare(original, source_digest, observed_id, operation=None):
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', source_digest) or not re.fullmatch(r'sha256:[a-f0-9]{64}', observed_id):
        raise ValueError('Observed repository digest and running image ID required')
    services = original['services']
    source = services['backend']['image']
    if not re.fullmatch(r'frappe/erpnext:v16\.\d+\.\d+', source):
        raise ValueError('An installed unpinned v16 image is required')
    target = source + '@' + source_digest
    network = original.get('networks', {}).get('default', {}).get('name')
    if network != 'ix-erpnext-catalog-restore-test_default':
        raise ValueError('Only the dedicated restore-test clone is supported')
    previous = services['initializer']['environment'].get('EXPECTED_UPGRADE_OPERATION')
    if not previous or not re.fullmatch(r'[a-f0-9]{32}', previous):
        raise ValueError('Expected successful restore operation required')
    operation = operation or uuid.uuid4().hex
    outputs = rehearsal(original, operation)
    common = dict(CATALOG_OPERATION_LAYOUT='catalog-upgrade-v1', SOURCE_IMAGE=source,
        TARGET_IMAGE=target, SOURCE_DIGEST=source_digest, OBSERVED_SOURCE_IMAGE_ID=observed_id,
        PREVIOUS_UPGRADE_OPERATION=previous)
    for filename, document in outputs.items():
        if 'rehearsal-job' in document['services']:
            job = document['services']['rehearsal-job']
            job['environment'].update(common)
            job['image'] = source + '@' + source_digest
            continue
        document['configs']['catalog_pinning_gate'] = {
            'content': (ROOT / 'pinning_gate.py').read_text(encoding='utf-8').replace('$', '$$')}
        for name in (*RUNTIME, 'initializer', 'bootstrap'):
            service = document['services'][name]
            service['image'] = target
            service['environment']['CATALOG_IMAGE'] = target
            if name in RUNTIME:
                continue
            service['environment'].update(common, SITE_NAME=services['frontend']['environment']['FRAPPE_SITE_NAME_HEADER'],
                OPERATION_ID=operation, UPGRADE_PHASE='migrate',
                EXPECTED_UPGRADE_OPERATION=operation, EXPECTED_UPGRADE_IMAGE=target,
                PINNING_GATE=name)
            service['entrypoint'] = ['/home/frappe/frappe-bench/env/bin/python', '/catalog/pinning-gate.py']
            service['command'] = []
            service['configs'] = [m for m in service['configs']
                if m.get('source') not in ('catalog_rehearsal', 'catalog_rehearsal_resume', 'catalog_pinning_gate')]
            service['configs'].extend([
                {'source': 'catalog_rehearsal', 'target': '/catalog/rehearsal.py', 'mode': 292},
                {'source': 'catalog_pinning_gate', 'target': '/catalog/pinning-gate.py', 'mode': 292}])
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed-yaml', type=Path, required=True)
    parser.add_argument('--source-digest', required=True)
    parser.add_argument('--observed-image-id', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    outputs = prepare(yaml.safe_load(args.installed_yaml.read_text(encoding='utf-8')),
        args.source_digest, args.observed_image_id)
    args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, document in outputs.items():
        path = args.output_dir / name
        with path.open('x', encoding='utf-8') as output:
            output.write('# PRIVATE: same-content pinning on restore-test clone only.\n')
            yaml.safe_dump(document, output, sort_keys=False)
        path.chmod(0o600)
    print('Created five private pinning stages. Nothing deployed.')


if __name__ == '__main__':
    main()
