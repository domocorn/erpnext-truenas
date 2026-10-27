"""Build a secret-free native catalog lab bundle in Linux using cached official tools."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from build_native_candidate import build, APP_NAME, PROFILES
from native_catalog_lab import tree_hash

SCRIPTS = Path(__file__).resolve().parent
IMAGE = 'ghcr.io/truenas/apps_validation:latest'


def official(root, *command, scripts=False):
    invocation = ['docker', 'run', '--rm', '--pull=never', '-e', 'FAKE_ENV=1',
                  '-e', 'PYTHONDONTWRITEBYTECODE=1', '-v', f'{root}:/workspace']
    if scripts:
        invocation += ['-v', f'{SCRIPTS}:/scripts:ro']
    subprocess.run([*invocation, IMAGE, *command], check=True)


def bundle(apps_root, output, work, profile='normal'):
    archive = output.with_suffix('.tar.gz')
    if output.exists() or work.exists() or archive.exists():
        raise RuntimeError('Choose new bundle and work paths; existing artifacts are preserved')
    output.mkdir(parents=True)
    work.mkdir(parents=True)
    built_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    app_name=PROFILES[profile]
    manifest = {'app': app_name, 'built_at_utc': built_at, 'entries': {}, 'app_files': {}}
    manifest['validator_image'] = json.loads(subprocess.check_output(
        ['docker', 'image', 'inspect', IMAGE, '--format', '{{json .RepoDigests}}'], text=True))
    for role in (('source',) if profile=='recovery' else ('source', 'target')):
        root = work/role
        build(apps_root, root, role, profile)
        official(root, 'apps_catalog_hash_generate', '--path=/workspace', '--train', 'community', '--app', app_name)
        official(root, 'python', '-c',
                 'from apps_validation.validate_dev_directory import validate_dev_directory_structure; '
                 f'validate_dev_directory_structure("/workspace", {{"community":["{app_name}"]}})')
        official(root, 'apps_catalog_update', 'publish', '--path=/workspace')
        official(root, 'python', '/scripts/package_native_index.py', '--path=/workspace',
                 '--built-at', built_at, '--app-name', app_name, scripts=True)
        destination = output/role
        destination.mkdir()
        for filename in ('catalog.json', 'lab-build.json'):
            shutil.copyfile(root/filename, destination/filename)
        shutil.copytree(root/'trains', destination/'trains')
        manifest['entries'][role] = json.loads((destination/'catalog.json').read_text())['community'][app_name]
        manifest['app_files'][role] = tree_hash(destination/'trains/community'/app_name)
    stager=(SCRIPTS/'native_catalog_lab.py').read_text()
    if profile!='normal':
        stager=stager.replace("APP = 'erpnext-native-lab'", f"APP = '{app_name}'")
        stager=stager.replace("INSTANCE = 'erpnext-native-test'", f"INSTANCE = 'erpnext-native-{profile}-test'")
        stager=stager.replace("Path('/root/erpnext-native-catalog-lab')", f"Path('/root/erpnext-native-{profile}-catalog-lab')")
    (output/'native_catalog_lab.py').write_text(stager)
    filename='NATIVE-CATALOG-TEST.md' if profile=='normal' else 'NATIVE-FAILURE-RECOVERY-TEST.md'
    shutil.copyfile(SCRIPTS/'docs/tests'/filename, output/filename)
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    with tarfile.open(archive, 'w:gz') as stream:
        stream.add(output, arcname=output.name)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name+'.sha256').write_text(digest+'  '+archive.name+'\n')
    print('Native lab bundle:', archive)
    print('SHA256:', digest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apps-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True)
    parser.add_argument('--profile',choices=tuple(PROFILES),default='normal')
    args = parser.parse_args()
    bundle(args.apps_root.resolve(), args.output_dir.resolve(), args.work_dir.resolve(),args.profile)
