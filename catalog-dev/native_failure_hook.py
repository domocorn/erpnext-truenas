"""TEST ONLY: fail an actual patch after a committed before_migrate fixture."""
import os
from pathlib import Path


def install():
    from patch_policy import TARGET
    if (os.environ.get('CATALOG_NATIVE_FAILURE_ACK') != 'disposable-native-failure' or
            os.environ.get('CATALOG_IMAGE') != TARGET):
        raise RuntimeError('Dedicated native failure candidate required')
    package = Path('/home/frappe/frappe-bench/apps/erpnext/erpnext')
    with (package/'catalog_native_failure.py').open('x') as output:
        output.write('''import frappe
from pathlib import Path

def fail():
    frappe.get_doc({'doctype':'ToDo', 'description':'Native failed migration fixture'}).insert(ignore_permissions=True)
    frappe.db.commit()
    Path('/home/frappe/frappe-bench/sites/.catalog-native-failure-entered').write_text('Committed before_migrate fixture.\\n')
    print('NATIVE FAILURE HOOK ENTERED: committed fixture; deliberate migration failure.', flush=True)
    raise RuntimeError('Deliberate disposable native migration failure')
''')
    with (package/'hooks.py').open('a') as output:
        output.write("\nbefore_migrate = ([before_migrate] if isinstance(before_migrate, str) else list(before_migrate)) if 'before_migrate' in globals() else []\nbefore_migrate.append('erpnext.catalog_native_failure.fail')\n")
