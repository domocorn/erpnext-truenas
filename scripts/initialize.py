"""Runs inside the official ERPNext container. Fresh installs only."""
import json
import os
from pathlib import Path
import re
import subprocess


def main():
    site = os.environ['SITE_NAME']
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,120}', site) or '..' in site:
        raise SystemExit('Invalid site name')
    root = Path('sites')
    marker = root / site / '.nas-initialized'
    pending = root / ('.nas-installing-' + site)

    def bench(*args):
        return subprocess.run(['bench', *args], check=True, capture_output=False)

    if pending.exists():
        raise SystemExit('A previous installation was interrupted. Inspect initializer logs; do not delete site data automatically.')
    if (root / site).exists():
        if not marker.exists():
            raise SystemExit('An unmanaged or incomplete site exists. Import is not supported by this prototype.')
        apps = subprocess.check_output(['bench', '--site', site, 'execute', 'frappe.get_installed_apps'], text=True)
        if 'erpnext' not in json.loads(apps):
            raise SystemExit('Existing site is missing ERPNext')
        print('Existing managed ERPNext site verified; skipping installation.', flush=True)
        return
    if not os.environ.get('ADMIN_PASSWORD') or not os.environ.get('DB_ROOT_PASSWORD'):
        raise SystemExit('Initial passwords are required')
    pending.write_text('Installation started; inspect logs if this marker remains.\n')
    bench('new-site', site, '--db-host', 'db', '--db-root-username', 'root',
          '--db-root-password', os.environ['DB_ROOT_PASSWORD'],
          '--admin-password', os.environ['ADMIN_PASSWORD'],
          '--mariadb-user-host-login-scope=%', '--install-app', 'erpnext')
    bench('--site', site, 'enable-scheduler')
    marker.write_text('Prototype initialized this site. Not an upgrade version marker.\n')
    pending.unlink()
    print('ERPNext installation complete.', flush=True)


if __name__ == '__main__':
    main()
