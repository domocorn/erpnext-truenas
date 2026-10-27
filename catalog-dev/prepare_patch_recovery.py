"""Recover a patch's old-image backup into a NEW old-version destination."""
import argparse
import copy
from pathlib import Path
import yaml
from patch_policy import SOURCE, TARGET
from prepare_healthcheck_update import RUNTIME
from prepare_restore import prepare as restore


def prepare(upgrade, apps_root, lab_root):
    if (upgrade.get('networks',{}).get('default',{}).get('name')!='ix-erpnext-catalog-patch-test_default'
            or upgrade['services']['backend']['image']!=TARGET
            or upgrade['services'].get('patch-backup',{}).get('image')!=SOURCE):
        raise ValueError('Exact reviewed patch plan required')
    source=copy.deepcopy(upgrade)
    for name in (*RUNTIME,'initializer','bootstrap'):
        source['services'][name]['image']=SOURCE
        source['services'][name]['environment']['CATALOG_IMAGE']=SOURCE
    return restore(source,apps_root,lab_root,18089,'erpnext-catalog-patch-recovery-test')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upgrade-yaml',required=True,type=Path)
    parser.add_argument('--apps-root',required=True,type=Path)
    parser.add_argument('--lab-root',required=True)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    documents=prepare(yaml.safe_load(args.upgrade_yaml.read_text()),args.apps_root,args.lab_root)
    args.output_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
    for name,document in documents.items():
        path=args.output_dir/name
        with path.open('x') as output: yaml.safe_dump(document,output,sort_keys=False)
        path.chmod(0o600)
    print('Prepared three private old-image patch recovery stages. Nothing deployed.')


if __name__=='__main__': main()
