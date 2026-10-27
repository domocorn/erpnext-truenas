"""Add catalog healthchecks to an exact installed YAML without regenerating credentials."""
import argparse
import copy
from pathlib import Path

import yaml
from render_catalog import render_legacy as render

RUNTIME = ('backend', 'frontend', 'websocket', 'queue-short', 'queue-long', 'scheduler')


def prepare_update(installed, apps_root):
    app = apps_root.resolve() / 'ix-dev/community/erpnext'
    values = yaml.safe_load((app / 'ix_values.yaml').read_text())
    values.update(yaml.safe_load((app / 'templates/test_values/basic-values.yaml').read_text()))
    values['ix_context'] = {'app_name': 'erpnext-catalog-test',
        'app_metadata': {'title': 'ERPNext', 'train': 'community'}}
    reference = render(values, apps_root)
    expected_image = reference['services']['frontend']['image']
    services = installed['services']
    if 'catalog_bootstrap' not in installed.get('configs', {}):
        raise ValueError('Expected the installed catalog draft, not standalone prototype YAML')
    if any(services[name]['image'] != expected_image for name in RUNTIME):
        raise ValueError('Runtime image differs from current template; image upgrades are unsupported')
    site = services['frontend']['environment']['FRAPPE_SITE_NAME_HEADER']
    updated = copy.deepcopy(installed)
    updated.setdefault('configs', {})['catalog_health'] = reference['configs']['catalog_health']
    for name in RUNTIME:
        service = updated['services'][name]
        service['healthcheck'] = reference['services'][name]['healthcheck']
        service.setdefault('environment', {})['SITE_NAME'] = site
        mounts = service.setdefault('configs', [])
        target = '/catalog/health.py'
        for mount in mounts:
            if isinstance(mount, dict) and mount.get('target') == target and mount.get('source') != 'catalog_health':
                raise ValueError('Healthcheck config mount conflicts with installed YAML')
        mounts[:] = [mount for mount in mounts if not (
            isinstance(mount, dict) and mount.get('source') == 'catalog_health')]
        mounts.extend(copy.deepcopy([mount for mount in reference['services'][name]['configs']
            if mount['source'] == 'catalog_health']))
    return updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed-yaml', type=Path, required=True)
    parser.add_argument('--apps-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.installed_yaml.resolve():
        parser.error('Use a separate output path; preserve the installed YAML')
    if args.output.exists():
        parser.error('Output exists; choose a new private output path')
    updated = prepare_update(yaml.safe_load(args.installed_yaml.read_text(encoding='utf-8')), args.apps_root)
    # Exclusive creation prevents accidental replacement of an existing plan.
    with args.output.open('x', encoding='utf-8') as output:
        output.write('# PRIVATE configuration. Do not commit.\n')
        yaml.safe_dump(updated, output, sort_keys=False)
    args.output.chmod(0o600)
    print('Prepared healthcheck-only update; retain the original installed YAML.')


if __name__ == '__main__':
    main()
