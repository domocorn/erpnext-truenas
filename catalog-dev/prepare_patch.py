"""Prepare the explicit v16.51.1-to-v16.52.1 graph on an isolated patch-test app."""
import copy
from pathlib import Path
from patch_policy import SOURCE, TARGET, SOURCE_DIGEST, SOURCE_ID
from prepare_healthcheck_update import RUNTIME
from prepare_rehearsal import prepare as rehearsal

ROOT = Path(__file__).resolve().parent


def prepare(source):
    if source.get('networks', {}).get('default', {}).get('name') != 'ix-erpnext-catalog-patch-test_default':
        raise ValueError('Dedicated patch-test app required')
    if source['services']['backend']['image'] != SOURCE:
        raise ValueError('Exact reviewed source image required')
    stages = rehearsal(source)
    result = stages['05-resume.yaml']
    result['configs'].pop('catalog_rehearsal_resume', None)
    for key, filename in [('catalog_patch_policy','patch_policy.py'),('catalog_patch_target','patch_target.py'),('catalog_patch_bootstrap','patch_bootstrap.py')]:
        result['configs'][key] = {'content': (ROOT/filename).read_text().replace('$','$$')}
    common = dict(CATALOG_OPERATION_LAYOUT='catalog-patch-v1', SOURCE_IMAGE=SOURCE,
        TARGET_IMAGE=TARGET, SOURCE_DIGEST=SOURCE_DIGEST, OBSERVED_SOURCE_IMAGE_ID=SOURCE_ID)
    policy_mount = {'source':'catalog_patch_policy','target':'/catalog/patch_policy.py','mode':292}
    job_mount = {'source':'catalog_rehearsal','target':'/catalog/rehearsal.py','mode':292}
    backup = copy.deepcopy(stages['01-backup.yaml']['services']['rehearsal-job'])
    backup['environment'].update(common)
    backup['configs'].append(copy.deepcopy(policy_mount))
    backup['depends_on']['bootstrap'] = {'condition':'service_completed_successfully'}
    result['services']['patch-backup'] = backup
    boot = result['services']['bootstrap']
    boot['entrypoint'][-1] = '/catalog/patch-bootstrap.py'
    boot['environment'].update(backup['environment'])
    boot['configs'] = [job_mount,policy_mount,{'source':'catalog_patch_bootstrap','target':'/catalog/patch-bootstrap.py','mode':292}]
    initializer = result['services']['initializer']
    initializer['image'] = TARGET
    initializer['entrypoint'][-1] = '/catalog/patch-target.py'
    initializer['environment'].update(common,UPGRADE_PHASE='migrate',SIMULATE_FAILURE='0',EXPECTED_UPGRADE_IMAGE=TARGET)
    initializer['configs'] = [m for m in initializer['configs'] if m['source']!='catalog_rehearsal_resume']
    initializer['configs'].extend([copy.deepcopy(policy_mount),{'source':'catalog_patch_target','target':'/catalog/patch-target.py','mode':292}])
    initializer['depends_on']['patch-backup'] = {'condition':'service_completed_successfully'}
    for name in RUNTIME:
        result['services'][name]['image'] = TARGET
        result['services'][name]['environment']['CATALOG_IMAGE'] = TARGET
    return result
