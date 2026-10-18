"""Generate a standalone TrueNAS custom-app YAML; never reads production config."""
import argparse
import copy
import getpass
from pathlib import Path
import re
import secrets
import yaml

ROOT = Path(__file__).resolve().parents[1]


def make_compose(site, port, admin, database):
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,120}', site) or '..' in site:
        raise ValueError('Use a lowercase site name containing letters, digits, dots and hyphens')
    if not 1024 <= port <= 65535:
        raise ValueError('Web port must be between 1024 and 65535')
    if len(admin) < 12:
        raise ValueError('Use an administrator password of at least 12 characters')
    # Compose interpolates dollars even in quoted YAML. Escape literal credentials.
    literal = lambda value: value.replace('$', '$$')
    image = 'frappe/erpnext:v16.51.1'
    base = dict(image=image, platform='linux/amd64', restart='unless-stopped',
                volumes=['sites:/home/frappe/frappe-bench/sites', 'logs:/home/frappe/frappe-bench/logs'])
    ready = {'initializer': {'condition': 'service_completed_successfully'}}
    def runtime(command=None):
        service = copy.deepcopy(base)
        service['depends_on'] = copy.deepcopy(ready)
        if command:
            service['command'] = command
        return service
    services = {
        'db': {
            'image': 'mariadb:11.8', 'restart': 'unless-stopped',
            'environment': {'MARIADB_ROOT_PASSWORD': literal(database), 'MARIADB_ROOT_HOST': '%'},
            'command': ['--character-set-server=utf8mb4', '--collation-server=utf8mb4_unicode_ci', '--skip-character-set-client-handshake'],
            'volumes': ['db-data:/var/lib/mysql'],
            'healthcheck': {'test': ['CMD', 'healthcheck.sh', '--connect', '--innodb_initialized'],
                            'interval': '10s', 'timeout': '5s', 'retries': 30, 'start_period': '30s'}},
    }
    for name in ('redis-cache', 'redis-queue'):
        service = {'image': 'redis:8.6-alpine', 'restart': 'unless-stopped',
                   'healthcheck': {'test': ['CMD', 'redis-cli', 'ping'], 'interval': '5s', 'timeout': '3s', 'retries': 30}}
        if name == 'redis-queue':
            service.update(command=['redis-server', '--appendonly', 'yes'], volumes=['redis-queue-data:/data'])
        services[name] = service
    config = copy.deepcopy(base)
    config.update(restart='no', entrypoint=['bash', '-ec'], depends_on={
        n: {'condition': 'service_healthy'} for n in ('db', 'redis-cache', 'redis-queue')}, command=[
        'ls -1 apps > sites/apps.txt\n'
        'bench set-config -g db_host db\n'
        'bench set-config -gp db_port 3306\n'
        'bench set-config -g redis_cache redis://redis-cache:6379\n'
        'bench set-config -g redis_queue redis://redis-queue:6379\n'
        'bench set-config -g redis_socketio redis://redis-queue:6379\n'
        'bench set-config -gp socketio_port 9000\n'
        'bench set-config -g chromium_path /usr/lib/chromium/chromium-headless-shell\n'])
    services['configurator'] = config
    init = copy.deepcopy(base)
    init.update(restart='no', depends_on={'configurator': {'condition': 'service_completed_successfully'}},
                entrypoint=['/home/frappe/frappe-bench/env/bin/python', '-c'],
                command=[(ROOT / 'scripts/initialize.py').read_text().replace('$', '$$')],
                environment={'SITE_NAME': site, 'ADMIN_PASSWORD': literal(admin), 'DB_ROOT_PASSWORD': literal(database)})
    services['initializer'] = init
    services['backend'] = runtime()
    services['websocket'] = runtime(['node', '/home/frappe/frappe-bench/apps/frappe/socketio.js'])
    services['queue-short'] = runtime(['bench', 'worker', '--queue', 'short,default'])
    services['queue-long'] = runtime(['bench', 'worker', '--queue', 'long'])
    services['scheduler'] = runtime(['bench', 'schedule'])
    frontend = runtime(['nginx-entrypoint.sh'])
    frontend.update(environment={'BACKEND': 'backend:8000', 'SOCKETIO': 'websocket:9000',
                     'FRAPPE_SITE_NAME_HEADER': site, 'NGINX_LISTEN_PORT': '8080',
                     'UPSTREAM_REAL_IP_ADDRESS': '127.0.0.1', 'UPSTREAM_REAL_IP_HEADER': 'X-Forwarded-For',
                     'UPSTREAM_REAL_IP_RECURSIVE': 'off', 'PROXY_READ_TIMEOUT': '120', 'CLIENT_MAX_BODY_SIZE': '50m'},
                    ports=[{'target': 8080, 'published': str(port), 'protocol': 'tcp'}])
    frontend['depends_on'].update({n: {'condition': 'service_started'} for n in ('backend', 'websocket')})
    services['frontend'] = frontend
    return {'services': services, 'volumes': {n: {} for n in ('sites', 'logs', 'db-data', 'redis-queue-data')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', default='erpnext.test')
    parser.add_argument('--port', type=int, default=18081)
    parser.add_argument('--output', default='generated/erpnext-test.yaml')
    args = parser.parse_args()
    password = getpass.getpass('Initial ERPNext Administrator password (12+ characters): ')
    if password != getpass.getpass('Confirm password: '):
        raise SystemExit('Passwords do not match')
    document = make_compose(args.site, args.port, password, secrets.token_urlsafe(36))
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('# PRIVATE: contains credentials. Do not commit or publish.\n' + yaml.safe_dump(document, sort_keys=False))
    path.chmod(0o600)
    print(f'Created {path}. Install in the TEST TrueNAS VM as erpnext-test. Never use production storage.')


if __name__ == '__main__':
    main()
