"""Render the ERPNext catalog template locally using the actual repository library.

Not a substitute for TrueNAS middleware/schema validation or official CI.
"""
import argparse
import copy
import getpass
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined



def render(values, apps_root):
    ROOT = Path(apps_root).resolve()
    APP = ROOT / 'ix-dev/community/erpnext'
    meta = yaml.safe_load((APP / 'app.yaml').read_text())
    version = meta['lib_version']
    library = ROOT / 'library' / version
    if not library.exists():
        raise RuntimeError('Matching library missing; sync the apps fork with upstream before rendering.')
    # Upstream detection uses os.uname; this preview runs off-host on Windows too.
    if not hasattr(os, 'uname'):
        from collections import namedtuple
        Uname = namedtuple('Uname', 'sysname nodename release version machine')
        os.uname = lambda: Uname('Windows', 'local', 'local-catalog-preview', '0', 'AMD64')
    spec = importlib.util.spec_from_file_location('erpnext_catalog_lib', library / '__init__.py', submodule_search_locations=[str(library)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules['erpnext_catalog_lib'] = pkg
    spec.loader.exec_module(pkg)
    render_module = importlib.import_module('erpnext_catalog_lib.render')
    env = Environment(loader=FileSystemLoader(APP / 'templates'), undefined=StrictUndefined, extensions=['jinja2.ext.do'])
    text = env.get_template('docker-compose.yaml').render(values=copy.deepcopy(values), ix_lib=SimpleNamespace(base=SimpleNamespace(render=render_module)))
    return json.loads(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apps-root', required=True, type=Path, help='Local clone of truenas/apps')
    parser.add_argument('--lab-root', required=True, help='Dedicated existing VM directory, e.g. /mnt/labpool/erpnext-catalog-test')
    parser.add_argument('--port', type=int, default=18084)
    parser.add_argument('--site', default='erpnext.localhost')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'generated/catalog-test.yaml')
    args = parser.parse_args()
    APP = args.apps_root.resolve() / 'ix-dev/community/erpnext'
    if args.output.exists():
        raise SystemExit('Output already exists: retain credentials; choose a new path for a fresh installation.')
    if not args.lab_root.startswith('/mnt/') or '..' in args.lab_root or args.lab_root.rstrip('/') in ('/mnt', '/mnt/labpool'):
        raise SystemExit('Use a dedicated directory below a test VM pool, not a pool root.')
    import re
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,120}', args.site) or '..' in args.site:
        raise SystemExit('Invalid site name')
    if not 1024 <= args.port <= 65535:
        raise SystemExit('Use a web port from 1024 to 65535')
    admin = getpass.getpass('Initial ERPNext Administrator password (12+ characters): ')
    db = getpass.getpass('New test database password (12+ characters): ')
    if min(len(admin), len(db)) < 12:
        raise SystemExit('Both passwords must be at least 12 characters')
    values = yaml.safe_load((APP / 'ix_values.yaml').read_text())
    values.update(erpnext={'site_name': args.site, 'admin_password': admin, 'db_password': db},
                  network={'web_port': {'bind_mode': 'published', 'port_number': args.port, 'host_ips': []}},
                  storage={}, labels=[], resources={'limits': {'cpus': 2, 'memory': 2048}},
                  ix_context={'app_name': 'erpnext-catalog-test', 'app_metadata': {'title': 'ERPNext', 'train': 'community'}})
    for name in ('sites', 'logs', 'db_data', 'queue_data'):
        values['storage'][name] = {'type': 'host_path', 'host_path_config': {'path': args.lab_root.rstrip('/') + '/' + name, 'auto_permissions': True, 'acl_enable': False}}
    document = render(values, args.apps_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('# PRIVATE lab configuration. Do not commit.\n' + yaml.safe_dump(document, sort_keys=False))
    args.output.chmod(0o600)
    print('Rendered with catalog library ' + yaml.safe_load((APP / 'app.yaml').read_text())['lib_version'])
    print('PRIVATE output: ' + str(args.output))
    print('Not official middleware validation. Read catalog-dev/README.md before deploying.')


if __name__ == '__main__':
    main()
