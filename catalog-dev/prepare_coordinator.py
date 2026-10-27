"""Consolidate the tested same-image lifecycle into one disposable-app deployment."""
import argparse
from pathlib import Path
import yaml
from prepare_rehearsal import prepare as rehearsal


def prepare(source):
    if source.get('networks', {}).get('default', {}).get('name') != 'ix-erpnext-catalog-interrupt-recovery-test_default':
        raise ValueError('Use only the successful interruption-recovery clone')
    documents = rehearsal(source)
    result = documents['05-resume.yaml']
    result['configs']['catalog_coordinator'] = {
        'content': Path(__file__).with_name('coordinator.py').read_text().replace('$', '$$')}
    result['configs'].pop('catalog_rehearsal_resume', None)
    initializer = result['services']['initializer']
    initializer['entrypoint'][-1] = '/catalog/coordinator.py'
    initializer['environment'].update(UPGRADE_PHASE='backup', SIMULATE_FAILURE='0')
    initializer['configs'] = [m for m in initializer['configs'] if m['source'] != 'catalog_rehearsal_resume']
    initializer['configs'].append({'source': 'catalog_coordinator', 'target': '/catalog/coordinator.py', 'mode': 292})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed-yaml', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path; preserve installed YAML')
    document = prepare(yaml.safe_load(args.installed_yaml.read_text()))
    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with args.output.open('x') as output:
        output.write('# PRIVATE: coordinated same-image lifecycle on recovered test clone only.\n')
        yaml.safe_dump(document, output, sort_keys=False)
    args.output.chmod(0o600)
    print('Prepared one private coordinated lifecycle YAML. Nothing deployed.')


if __name__ == '__main__':
    main()
