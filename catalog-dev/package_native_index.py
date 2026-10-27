"""Run inside the official validator image; index an uncommitted lab build.

Use the explicitly supplied UTC build date where the upstream indexer expects
a Git commit date. No validation is skipped and no Git history is manufactured.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path


def package(root, built_at, app_name='erpnext-native-lab'):
    from apps_ci.scripts.catalog_update import update_catalog_file
    import catalog_reader.app as reader
    datetime.strptime(built_at, '%Y-%m-%d %H:%M:%S')
    original = reader.get_last_updated_date
    reader.get_last_updated_date = lambda *_: built_at
    try:
        update_catalog_file(str(root))
    finally:
        reader.get_last_updated_date = original
    data = json.loads((root/'catalog.json').read_text())
    entry = data['community'][app_name]
    versions = json.loads((root/'trains/community'/app_name/'app_versions.json').read_text())
    if not entry['healthy'] or not versions or any(not v['healthy'] for v in versions.values()):
        raise RuntimeError('Unhealthy native lab package')
    (root/'lab-build.json').write_text(json.dumps({
        'purpose': 'Unpublished disposable native catalog test',
        'built_at_utc': built_at,
        'date_source': 'Explicit build timestamp; not an upstream Git commit date',
        'versions': sorted(versions),
    }, indent=2)+'\n')
    print('Healthy native lab versions:', ', '.join(sorted(versions)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', type=Path, required=True)
    parser.add_argument('--built-at', required=True)
    parser.add_argument('--app-name', default='erpnext-native-lab')
    args = parser.parse_args()
    package(args.path, args.built_at, args.app_name)
