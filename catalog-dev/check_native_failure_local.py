"""Real Docker integration check in dedicated WSL storage; never targets the VM."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import yaml
from render_catalog import render
from native_failure_lab import FIXTURE, VERIFY, RUNTIME
from native_policy import operation_id
from patch_policy import SOURCE, TARGET


def command(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def check(work, plans, resume=False):
    if (work.exists() or plans.exists()) and not resume:
        raise RuntimeError('Dedicated new WSL test paths required')
    if not str(work).startswith('/mnt/erpnext-wsl-lab/') or not str(plans).startswith('/var/tmp/'):
        raise RuntimeError('This check is restricted to isolated local WSL storage')
    work.mkdir(parents=True,exist_ok=resume)
    plans.mkdir(mode=0o700,exist_ok=resume)
    if resume:
        state=json.loads((work/'failure/sites/erpnext.localhost/.nas-upgrade-state.json').read_text())
        if state.get('status')!='resumed' or state.get('installation')!='fresh':
            raise RuntimeError('Resume is only for a completed fresh source before deliberate failure')
    credentials={key:secrets.token_urlsafe(24) for key in ('admin_password','db_password')}
    files={}
    for profile,role,port in [('failure','source',18091),('failure','target',18091),('recovery','source',18092)]:
        if resume:
            files[profile,role]=plans/(profile+'-'+role+'.yaml')
            if not files[profile,role].is_file(): raise RuntimeError('Missing preserved local plan')
            continue
        root=Path('/var/tmp')/f'erpnext-native-{profile}-{role}-01'
        app_name='erpnext-native-'+profile+'-lab'
        app=root/'ix-dev/community'/app_name
        values=yaml.safe_load((app/'ix_values.yaml').read_text())
        values.update(yaml.safe_load((app/'templates/test_values/basic-values.yaml').read_text()))
        values['erpnext'].update(credentials if profile=='failure' else
            {key:secrets.token_urlsafe(24) for key in credentials})
        values['network']['web_port']['port_number']=port
        if profile=='recovery':
            values['erpnext']['recovery_path']=str(work/'failure/sites/.catalog-recovery'/operation_id('erpnext.localhost',TARGET))
        for key in ('sites','logs','db_data','queue_data'):
            values['storage'][key]={'type':'host_path','host_path_config':{
                'path':str(work/profile/key),'auto_permissions':True,'acl_enable':False}}
        project='erpnext-native-'+profile+'-local'
        values['ix_context']={'app_name':project,'app_metadata':{'title':app_name,'train':'community'}}
        document=render(values,root,app_name)
        document['networks']={'default':{'name':project+'_default'}}
        path=plans/(profile+'-'+role+'.yaml')
        path.write_text(yaml.safe_dump(document,sort_keys=False)); path.chmod(0o600)
        files[profile,role]=path
        for key in ('sites','logs','db_data','queue_data'):
            folder=work/profile/key
            folder.mkdir(parents=True,exist_ok=True)
            os.chown(folder,999 if key=='db_data' else 1000,999 if key=='db_data' else 1000)

    def compose(profile,role,*args,check=True):
        return subprocess.run(['docker','compose','-p','erpnext-native-'+profile+'-local',
            '-f',str(files[profile,role]),*args],text=True,capture_output=True,check=check)

    def backend(profile):
        return compose(profile,'source','ps','-q','backend').stdout.strip()

    def execute(profile,program):
        return command('docker','exec','-i',backend(profile),'/home/frappe/frappe-bench/env/bin/python',
                       '-c','import sys; exec(sys.stdin.read())',input=program,capture_output=True)

    try:
        compose('failure','source','up','-d','--wait','--wait-timeout','600')
        if not (work/'failure/sites/.catalog-native-failure-fixture.json').exists():
            print(execute('failure',FIXTURE).stdout,flush=True)
        command('docker','exec',backend('failure'),'bench','--site','erpnext.localhost','set-config','pause_scheduler','1',capture_output=True)
        compose('failure','source','down')
        failure=compose('failure','target','up','-d','--wait','--wait-timeout','600',check=False)
        if failure.returncode==0:
            raise RuntimeError('Deliberate failed upgrade unexpectedly succeeded')
        sites=work/'failure/sites'
        state_path=sites/'erpnext.localhost/.nas-upgrade-state.json'
        state=json.loads(state_path.read_text())
        assert state['status']=='migrating'
        assert (sites/'.catalog-native-failure-entered').is_file()
        assert (sites/'.catalog-image').read_text().strip()==SOURCE
        for service in RUNTIME:
            assert not compose('failure','target','ps','--status','running','-q',service).stdout.strip()
        print('Actual native migration failed after its committed fixture; runtime remains blocked.',flush=True)
        compose('failure','target','down')
        repeat=compose('failure','target','up','-d','--wait','--wait-timeout','600',check=False)
        assert repeat.returncode!=0
        assert json.loads(state_path.read_text())==state
        print('Unchanged native restart refused the interrupted migration.',flush=True)
        compose('recovery','source','up','-d','--wait','--wait-timeout','600')
        shutil.copyfile(sites/'.catalog-native-failure-fixture.json',work/'recovery/sites/.catalog-native-failure-fixture.json')
        print(execute('recovery',VERIFY).stdout,flush=True)
        compose('recovery','source','down')
        compose('recovery','source','up','-d','--wait','--wait-timeout','600')
        print(execute('recovery',VERIFY).stdout,flush=True)
        assert json.loads(state_path.read_text())==state
        print('Independent native recovery and repeated restart passed; failed source preserved.',flush=True)
    except Exception:
        for profile,role in [('failure','target'),('recovery','source')]:
            print(compose(profile,role,'logs','--tail','25','bootstrap','upgrade-backup','initializer',check=False).stdout)
        raise
    finally:
        for profile,role in [('failure','target'),('recovery','source')]:
            compose(profile,role,'down',check=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--storage',type=Path,required=True)
    parser.add_argument('--plans',type=Path,required=True)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    check(args.storage,args.plans,args.resume)
