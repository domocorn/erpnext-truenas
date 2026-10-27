"""Assemble the two validated native lab profiles and their host helper."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
from native_catalog_lab import tree_hash


def assemble(generated):
    output=generated/'erpnext-native-failure-recovery-01'
    if output.exists() or output.with_suffix('.tar.gz').exists():
        raise RuntimeError('Preserve existing artifacts; use a new build directory')
    output.mkdir()
    for profile in ('failure','recovery'):
        source=generated/('erpnext-native-'+profile+'-01')
        manifest=json.loads((source/'manifest.json').read_text())
        for role,hashes in manifest['app_files'].items():
            if tree_hash(source/role/'trains/community'/manifest['app'])!=hashes:
                raise RuntimeError('Profile manifest verification failed')
        shutil.copytree(source,output/profile)
    scripts=Path(__file__).resolve().parent
    for filename in ('native_failure_lab.py','native_catalog_lab.py','native_policy.py',
                     'restore_job.py','patch_policy.py','NATIVE-FAILURE-RECOVERY-TEST.md'):
        source=scripts/'docs/tests'/filename if filename.endswith('.md') else scripts/filename
        shutil.copyfile(source,output/filename)
    archive=output.with_suffix('.tar.gz')
    with tarfile.open(archive,'w:gz') as stream:
        stream.add(output,arcname=output.name)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name+'.sha256').write_text(digest+'  '+archive.name+'\n')
    print('Combined native failure/recovery bundle:',archive)
    print('SHA256:',digest)


if __name__=='__main__':
    assemble(Path(__file__).resolve().parent/'generated')
