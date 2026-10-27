"""TEST ONLY: install an ephemeral before_migrate hook in this job container."""
import os
from pathlib import Path
import runpy


def main():
    if os.environ.get('INTERRUPTION_TEST_ACK') != 'disposable-recovery-clone':
        raise RuntimeError('Explicit disposable-clone interruption acknowledgement required')
    if os.environ.get('UPGRADE_PHASE') != 'migrate' or os.environ.get('SOURCE_IMAGE') != os.environ.get('TARGET_IMAGE'):
        raise RuntimeError('Only a same-image migration interruption is supported')
    package = Path('/home/frappe/frappe-bench/apps/erpnext/erpnext')
    fixture = package / 'catalog_interrupt_fixture.py'
    with fixture.open('x') as output:
        output.write('''import os
import time
from pathlib import Path
import frappe

def interrupt():
    operation = os.environ['OPERATION_ID']
    description = 'Catalog interrupted migration fixture ' + operation
    frappe.get_doc({'doctype': 'ToDo', 'description': description}).insert(ignore_permissions=True)
    frappe.db.commit()
    path = Path('/home/frappe/frappe-bench/sites') / ('.catalog-interrupt-entered-' + operation)
    with path.open('x') as marker:
        marker.write('before_migrate hook committed its fixture; kill only the test job container.\\n')
        marker.flush()
        os.fsync(marker.fileno())
    print('INTERRUPTION HOOK ENTERED; fixture committed. Awaiting test-container kill.', flush=True)
    while True:
        time.sleep(1)
''')
    with (package / 'hooks.py').open('a') as output:
        output.write("\nbefore_migrate = ([before_migrate] if isinstance(before_migrate, str) else list(before_migrate)) if 'before_migrate' in globals() else []\nbefore_migrate.append('erpnext.catalog_interrupt_fixture.interrupt')\n")
    runpy.run_path('/catalog/rehearsal.py', run_name='__main__')


if __name__ == '__main__':
    main()
