"""Apply warm worker stop and queue migration checks to the successful patch lab."""
import argparse
from pathlib import Path
import yaml
from prepare_runtime_update import prepare_runtime_update
from compose_output import dump_private_compose

ROOT = Path(__file__).resolve().parent


def prepare(source, apps_root):
    if source.get('networks',{}).get('default',{}).get('name') != 'ix-erpnext-catalog-patch-test_default':
        raise ValueError('Only the successful isolated patch-test app is supported')
    result = prepare_runtime_update(source, apps_root)
    result['configs']['catalog_rehearsal'] = {'content':(ROOT/'rehearsal_job.py').read_text().replace('$','$$')}
    result['configs']['catalog_queue_guard'] = {'content':(ROOT/'queue_guard.py').read_text().replace('$','$$')}
    result['configs']['catalog_worker_drain_test'] = {'content':(ROOT/'worker_drain_fixture.py').read_text().replace('$','$$')}
    for name in ('queue-short','queue-long'):
        result['services'][name]['stop_grace_period']='120s'
    for name,service in result['services'].items():
        mounts=service.get('configs',[])
        if name=='backend' or any(m.get('source')=='catalog_rehearsal' for m in mounts):
            mounts[:]=[m for m in mounts if m.get('source')!='catalog_queue_guard']
            mounts.append({'source':'catalog_queue_guard','target':'/catalog/queue_guard.py','mode':292})
    mounts=result['services']['backend']['configs']
    mounts[:]=[m for m in mounts if m.get('source')!='catalog_worker_drain_test']
    mounts.append({'source':'catalog_worker_drain_test','target':'/catalog/worker-drain-test.py','mode':292})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed-yaml',type=Path,required=True)
    parser.add_argument('--apps-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('Choose a new output path; preserve installed YAML')
    result=prepare(yaml.safe_load(args.installed_yaml.read_text()),args.apps_root)
    serialized=dump_private_compose(result)
    with args.output.open('x',newline='\n') as output: output.write(serialized)
    args.output.chmod(0o600)
    print('Prepared private warm-worker/queue-guard update. Nothing deployed.')


if __name__=='__main__': main()
