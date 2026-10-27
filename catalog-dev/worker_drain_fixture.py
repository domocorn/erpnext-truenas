"""Controlled RQ sleep fixture for the disposable patch-test app only."""
import argparse
import json
import os
from pathlib import Path
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('enqueue','status','guard'))
    parser.add_argument('--disposable-patch-test',action='store_true',required=True)
    args=parser.parse_args()
    os.chdir('/home/frappe/frappe-bench/sites')
    if args.action=='guard':
        from queue_guard import require_empty
        require_empty()
        print('QUEUE GATE PASSED')
        return
    import frappe
    from frappe.utils.background_jobs import get_queue
    from rq.job import Job
    frappe.init(site=os.environ['SITE_NAME'],sites_path='/home/frappe/frappe-bench/sites')
    try:
        queue=get_queue('short')
        path=Path('.catalog-worker-grace-test.json')
        if args.action=='enqueue' and not path.exists():
            job=queue.enqueue('time.sleep',60,job_timeout=90,result_ttl=86400)
            with path.open('x') as output: json.dump({'job_id':job.id},output)
            for attempt in range(30):
                if job.get_status(refresh=True)=='started':
                    print('STARTED: stop the patch-test app now; job runs for 60 seconds.')
                    return
                time.sleep(1)
            raise RuntimeError('Fixture did not start; inspect worker health')
        job=Job.fetch(json.loads(path.read_text())['job_id'],connection=queue.connection)
        status=job.get_status(refresh=True)
        print('Fixture status: '+str(getattr(status,'value',status)))
    finally:
        frappe.destroy()


if __name__=='__main__':
    try: main()
    except Exception as error:
        print('Worker fixture/gate blocked: '+type(error).__name__,flush=True)
        raise SystemExit(1)
