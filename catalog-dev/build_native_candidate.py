"""Build an isolated catalog candidate from the real app template plus native hooks."""
import argparse
from pathlib import Path
import shutil
import yaml
from patch_policy import SOURCE,TARGET

ROOT=Path(__file__).resolve().parent
APP_NAME='erpnext-native-lab'
PROFILES = {'normal': APP_NAME, 'failure': 'erpnext-native-failure-lab',
            'recovery': 'erpnext-native-recovery-lab'}


def build(apps_root, output, role, profile='normal'):
    if output.exists(): raise ValueError('Choose a new candidate directory')
    base=apps_root/'ix-dev/community/erpnext'
    app_name=PROFILES[profile]
    destination=output/'ix-dev/community'/app_name
    shutil.copytree(base,destination,ignore=shutil.ignore_patterns('library','rendered','__pycache__'))
    metadata=yaml.safe_load((destination/'app.yaml').read_text())
    metadata.update(name=app_name,title='ERPNext Native '+({'normal':'Lab','failure':'Failure Lab','recovery':'Recovery Lab'}[profile]),version='0.9.0' if role=='source' else '1.0.0',
        app_version='16.51.0' if role=='source' else '16.51.1')
    (destination/'app.yaml').write_text(yaml.safe_dump(metadata,sort_keys=False))
    values=yaml.safe_load((destination/'ix_values.yaml').read_text())
    values['images']['image']['tag']=(SOURCE if role=='source' else TARGET).split(':',1)[1]
    values['images']['previous_image']={'repository':'frappe/erpnext','tag':SOURCE.split(':',1)[1]}
    (destination/'ix_values.yaml').write_text(yaml.safe_dump(values,sort_keys=False))
    template=destination/'templates/docker-compose.yaml'
    text=template.read_text()
    anchor='{{ tpl.render() | tojson }}'
    if text.count(anchor)!=1: raise ValueError('Base template render anchor changed')
    if "{% include 'macros/native-integration.yaml' %}" not in text:
        text=text.replace(anchor,"{% include 'macros/native-integration.yaml' %}\n"+anchor)
    template.write_text(text)
    shutil.copyfile(ROOT/'native_integration.yaml',destination/'templates/macros/native-integration.yaml')
    scripts=[]
    for macro,filename in [('native_script','native_lifecycle.py'),('native_policy_script','native_policy.py'),
            ('native_job_script','rehearsal_job.py'),('native_patch_policy_script','patch_policy.py'),
            ('native_patch_target_script','patch_target.py'),('native_queue_guard_script','queue_guard.py')]:
        body=(ROOT/filename).read_text()
        if filename=='native_lifecycle.py' and profile=='failure' and role=='target':
            anchor="elif action=='initialize': initialize(root,lambda:runpy.run_path('/catalog/initialize.py',run_name='__main__'))"
            if body.count(anchor)!=1: raise ValueError('Native failure injection anchor changed')
            body=body.replace(anchor,"elif action=='initialize':\n            from native_failure_hook import install\n            install()\n            initialize(root,lambda:runpy.run_path('/catalog/initialize.py',run_name='__main__'))")
        if '{{' in body or '{%' in body: raise ValueError('Unexpected Jinja tokens in script')
        scripts.append('{% macro '+macro+'() %}\n'+body+'\n{% endmacro %}\n')
    (destination/'templates/macros/native_scripts.py').write_text('\n'.join(scripts))
    runtime=destination/'templates/macros/runtime.py'
    text=runtime.read_text()
    anchor="os.environ.get('EXPECTED_UPGRADE_OPERATION'))"
    helper="""def expected_operation():
    explicit = os.environ.get('EXPECTED_UPGRADE_OPERATION')
    if explicit:
        return explicit
    if os.environ.get('CATALOG_NATIVE_LIFECYCLE') == '1':
        from native_policy import operation_id
        return operation_id(os.environ['SITE_NAME'], os.environ['CATALOG_IMAGE'])
    return None


"""
    if 'def expected_operation():' not in text:
        if text.count(anchor)!=1: raise ValueError('Runtime operation anchor changed')
        text=text.replace(anchor,'expected_operation())').replace('def run():',helper+'def run():')
    elif helper not in text:
        raise ValueError('Integrated runtime operation helper changed')
    runtime.write_text(text)
    questions=destination/'questions.yaml'
    schema=yaml.safe_load(questions.read_text())
    def add_label(value):
        if isinstance(value,dict):
            enums=value.get('enum',[])
            if (isinstance(enums,list) and any(isinstance(item,dict) and item.get('value')=='initializer' for item in enums)
                    and not any(isinstance(item,dict) and item.get('value')=='upgrade-backup' for item in enums)):
                enums.append({'value':'upgrade-backup','description':'upgrade-backup'})
            for item in value.values(): add_label(item)
        elif isinstance(value,list):
            for item in value: add_label(item)
    add_label(schema)
    extra=[]
    if profile=='failure' and role=='target':
        body=(ROOT/'native_failure_hook.py').read_text()
        scripts.append('{% macro native_failure_script() %}\n'+body+'\n{% endmacro %}\n')
        extra.append("{% from 'macros/native_scripts.py' import native_failure_script %}\n{% do init.environment.add_env('CATALOG_NATIVE_FAILURE_ACK', 'disposable-native-failure') %}\n{% do init.configs.add('catalog_native_failure', native_failure_script(), '/catalog/native_failure_hook.py', '0444') %}\n")
    if profile=='recovery':
        for macro,filename in [('native_restore_script','restore_job.py'),('native_recovery_script','native_recovery_entry.py')]:
            scripts.append('{% macro '+macro+'() %}\n'+(ROOT/filename).read_text()+'\n{% endmacro %}\n')
        schema['questions'][0]['schema']['attrs'].append(dict(variable='recovery_path', label='Lab Recovery Backup Directory',
            description='Read-only backup directory from the disposable native failure test only.',
            schema=dict(type='string', required=True, default='/mnt/labpool/native-recovery-backup')))
        extra.append("""{% from 'macros/native_scripts.py' import native_restore_script, native_recovery_script %}
{% do init.set_entrypoint(['/home/frappe/frappe-bench/env/bin/python', '/catalog/native_recovery.py']) %}
{% do init.set_command([]) %}
{% do init.configs.add('catalog_native_restore', native_restore_script(), '/catalog/restore_job.py', '0444') %}
{% do init.configs.add('catalog_native_recovery', native_recovery_script(), '/catalog/native_recovery.py', '0444') %}
{% do init.add_storage('/recovery', {'type':'host_path', 'read_only':true, 'host_path_config':{'path':values.erpnext.recovery_path, 'create_host_path':false}}) %}
""")
        test_values=destination/'templates/test_values/basic-values.yaml'
        fixture=yaml.safe_load(test_values.read_text())
        fixture['erpnext']['recovery_path']='/mnt/labpool/native-recovery-backup'
        test_values.write_text(yaml.safe_dump(fixture,sort_keys=False))
    (destination/'templates/macros/native_scripts.py').write_text('\n'.join(scripts))
    if extra:
        integration=destination/'templates/macros/native-integration.yaml'
        integration.write_text(integration.read_text()+'\n'+'\n'.join(extra))
    questions.write_text(yaml.safe_dump(schema,sort_keys=False))
    version=metadata['lib_version']
    shutil.copytree(apps_root/'library'/version,output/'library'/version,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(apps_root/'.github/scripts',output/'.github/scripts',ignore=shutil.ignore_patterns('__pycache__'))
    print('Built isolated native',role,'candidate:',output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apps-root',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--role',choices=('source','target'),required=True)
    parser.add_argument('--profile',choices=tuple(PROFILES),default='normal')
    args=parser.parse_args()
    build(args.apps_root.resolve(),args.output_dir.resolve(),args.role,args.profile)


if __name__=='__main__': main()
