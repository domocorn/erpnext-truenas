"""Prepare same-image runtime guards from the exact installed catalog YAML."""
import argparse
import copy
from pathlib import Path

import yaml
from prepare_healthcheck_update import prepare_update, RUNTIME
from render_catalog import render_legacy as render


def prepare_runtime_update(installed, apps_root):
    updated = prepare_update(installed, apps_root)
    app = apps_root.resolve() / 'ix-dev/community/erpnext'
    values = yaml.safe_load((app / 'ix_values.yaml').read_text())
    values.update(yaml.safe_load((app / 'templates/test_values/basic-values.yaml').read_text()))
    values['ix_context'] = {'app_name': 'erpnext-catalog-test',
        'app_metadata': {'title': 'ERPNext', 'train': 'community'}}
    reference = render(values, apps_root)
    updated['configs']['catalog_runtime'] = reference['configs']['catalog_runtime']
    operation = installed['services']['initializer'].get('environment', {}).get('EXPECTED_UPGRADE_OPERATION')
    for name in RUNTIME:
        service = updated['services'][name]
        expected_entrypoint = reference['services'][name]['entrypoint']
        if service.get('entrypoint') not in (None, [], expected_entrypoint):
            raise ValueError('Custom runtime entrypoint requires manual review: ' + name)
        service['entrypoint'] = copy.deepcopy(expected_entrypoint)
        if not service.get('command'):
            service['command'] = copy.deepcopy(reference['services'][name]['command'])
        service['environment']['CATALOG_IMAGE'] = service['image']
        if operation:
            service['environment']['EXPECTED_UPGRADE_OPERATION'] = operation
        mounts = service.setdefault('configs', [])
        if any(isinstance(m, dict) and m.get('target') == '/catalog/runtime.py'
               and m.get('source') != 'catalog_runtime' for m in mounts):
            raise ValueError('Runtime config mount conflict')
        mounts[:] = [m for m in mounts if not (isinstance(m, dict) and m.get('source') == 'catalog_runtime')]
        mounts.extend(copy.deepcopy([m for m in reference['services'][name]['configs']
            if m['source'] == 'catalog_runtime']))
    return updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed-yaml', type=Path, required=True)
    parser.add_argument('--apps-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.installed_yaml.resolve() or args.output.exists():
        parser.error('Use a new output path; preserve the installed YAML')
    installed = yaml.safe_load(args.installed_yaml.read_text(encoding='utf-8'))
    updated = prepare_runtime_update(installed, args.apps_root)
    with args.output.open('x', encoding='utf-8') as output:
        output.write('# PRIVATE same-image runtime guard update. Do not commit.\n')
        yaml.safe_dump(updated, output, sort_keys=False)
    args.output.chmod(0o600)
    print('Prepared same-image runtime guards. No migration or deployment performed.')


if __name__ == '__main__':
    main()
