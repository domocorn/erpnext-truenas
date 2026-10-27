"""Prepare a destructive interruption rehearsal ONLY on the disposable recovery clone."""
import argparse
import copy
from pathlib import Path
import yaml
from prepare_rehearsal import prepare as rehearsal


def prepare(source):
    if source.get('networks', {}).get('default', {}).get('name') != 'ix-erpnext-catalog-pinned-recovery-test_default':
        raise ValueError('Only the dedicated pinned recovery clone is supported')
    documents = rehearsal(source)
    interrupted = copy.deepcopy(documents['04-migrate.yaml'])
    interrupted['configs']['catalog_interruption'] = {
        'content': Path(__file__).with_name('interruption_job.py').read_text().replace('$', '$$')}
    job = interrupted['services']['rehearsal-job']
    job['entrypoint'][-1] = '/catalog/interruption.py'
    job['environment']['INTERRUPTION_TEST_ACK'] = 'disposable-recovery-clone'
    job['configs'].append({'source': 'catalog_interruption', 'target': '/catalog/interruption.py', 'mode': 292})
    return {'01-backup.yaml': documents['01-backup.yaml'],
        '02-interrupt-migration.yaml': interrupted,
        '03-blocked-resume.yaml': documents['03-verify-startup-blocked.yaml'],
        '04-blocked-retry.yaml': documents['04-migrate.yaml']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed-yaml', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--disposable-recovery-clone', action='store_true', required=True)
    args = parser.parse_args()
    documents = prepare(yaml.safe_load(args.installed_yaml.read_text()))
    args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, document in documents.items():
        path = args.output_dir / name
        with path.open('x') as output:
            output.write('# PRIVATE DESTRUCTIVE TEST: disposable pinned recovery clone ONLY.\n')
            yaml.safe_dump(document, output, sort_keys=False)
        path.chmod(0o600)
    print('Prepared four interruption stages. No deployment performed.')


if __name__ == '__main__':
    main()
