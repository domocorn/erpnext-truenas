"""Prepare a NEW older-version patch lab, never downgrade an existing site."""
import argparse
from pathlib import Path, PurePosixPath
import secrets
import yaml
from patch_policy import SOURCE
from prepare_patch import prepare
from render_catalog import render_legacy as render


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apps-root',type=Path,required=True)
    parser.add_argument('--lab-root',required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    root=PurePosixPath(args.lab_root)
    if not root.is_absolute() or len(root.parts)<4 or root.parts[1]!='mnt' or '..' in root.parts:
        parser.error('Dedicated new lab directory beneath /mnt/pool required')
    values=yaml.safe_load((args.apps_root/'ix-dev/community/erpnext/ix_values.yaml').read_text())
    values['images']['image']['tag']=SOURCE.split(':',1)[1]
    values.update(erpnext={'site_name':'erpnext.localhost','admin_password':secrets.token_urlsafe(24),'db_password':secrets.token_urlsafe(24)},
        labels=[],storage={},resources={'limits':{'cpus':2,'memory':2048}},
        network={'web_port':{'bind_mode':'published','port_number':18088,'host_ips':[]}},
        ix_context={'app_name':'erpnext-catalog-patch-test','app_metadata':{'title':'ERPNext Patch Test','train':'community'}})
    for name in ('sites','logs','db_data','queue_data'):
        values['storage'][name]={'type':'host_path','host_path_config':{'path':str(root/name),'auto_permissions':True,'acl_enable':False}}
    source=render(values,args.apps_root)
    source['networks']={'default':{'name':'ix-erpnext-catalog-patch-test_default'}}
    documents={'01-initialize-source.yaml':source,'02-upgrade.yaml':prepare(source)}
    args.output_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
    for name,document in documents.items():
        path=args.output_dir/name
        with path.open('x') as output:
            output.write('# PRIVATE isolated real patch test. NEW app/storage only.\n')
            yaml.safe_dump(document,output,sort_keys=False)
        path.chmod(0o600)
    print('Prepared two private patch-lab files. Nothing deployed.')


if __name__=='__main__': main()
