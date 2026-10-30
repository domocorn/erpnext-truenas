"""Thin upstream integration: render checks, not runtime acceptance."""
import argparse
from pathlib import Path
import sys
import unittest
import yaml
from render_catalog import render

parser=argparse.ArgumentParser()
parser.add_argument('--apps-root',required=True,type=Path)
args,remaining=parser.parse_known_args()
sys.argv=[sys.argv[0],*remaining]
APP=args.apps_root.resolve()/'ix-dev/community/erpnext'

class ThinCatalogTests(unittest.TestCase):
    def setUp(self):
        self.values=yaml.safe_load((APP/'ix_values.yaml').read_text())
        self.values.update(yaml.safe_load((APP/'templates/test_values/basic-values.yaml').read_text()))
        self.values['ix_context']={'app_name':'erpnext-thin-test','app_metadata':{'title':'ERPNext','train':'community'}}

    def test_no_embedded_application_code_or_entrypoint_wrappers(self):
        doc=render(self.values,args.apps_root)
        self.assertEqual(set(doc.get('configs',{})), {'permissions_actions_data'})
        import json
        self.assertIsInstance(json.loads(doc['configs']['permissions_actions_data']['content']),list)
        self.assertFalse((APP/'templates/macros').exists())
        for name,service in doc['services'].items():
            if name not in ('configurator','permissions'):
                self.assertFalse(service.get('entrypoint'),name)
            self.assertFalse(service.get('privileged'),name)
        text=yaml.safe_dump(doc)
        for forbidden in ['/catalog/','/var/run/docker.sock','CATALOG_IMAGE','EXPECTED_UPGRADE']:
            self.assertNotIn(forbidden,text)

    def test_upstream_commands_and_dependencies(self):
        services=render(self.values,args.apps_root)['services']
        self.assertEqual(set(services),{'permissions','db','redis-cache','redis-queue','configurator','backend','frontend','websocket','queue-short','queue-long','scheduler'})
        for name in ('backend','frontend','websocket','queue-short','queue-long','scheduler'):
            self.assertEqual(services[name]['depends_on']['configurator']['condition'],'service_completed_successfully')
        config=services['configurator']
        self.assertEqual(config['entrypoint'],['bash','-ec'])
        self.assertIn('bench set-config -g db_host "$$DB_HOST"',config['command'][0])
        self.assertNotIn('new-site',config['command'][0])
        self.assertNotIn('migrate',config['command'][0])
        self.assertEqual(services['queue-long']['command'],['bench','worker','--queue','long,default,short'])

    def test_storage_images_ports_and_literal_password(self):
        self.values['erpnext']['db_password']='test$literal-password'
        for key in ('sites','logs','db_data','queue_data'):
            self.values['storage'][key]={'type':'host_path','host_path_config':{'path':'/mnt/labpool/thin/'+key,'auto_permissions':True}}
        services=render(self.values,args.apps_root)['services']
        image='frappe/erpnext:'+self.values['images']['image']['tag']
        self.assertIn('@sha256:',image)
        for name in ('configurator','backend','frontend','websocket','queue-short','queue-long','scheduler'):
            self.assertEqual(services[name]['image'],image)
            self.assertEqual(services[name]['user'],'1000:1000')
        self.assertIn(0,services['frontend']['group_add'])
        self.assertEqual([n for n,s in services.items() if s.get('ports')],['frontend'])
        self.assertEqual(services['frontend']['ports'][0]['target'],8080)
        self.assertEqual(services['db']['environment']['MARIADB_ROOT_PASSWORD'],'test$$literal-password')
        self.assertEqual(services['backend']['volumes'][0]['type'],'bind')

if __name__=='__main__':unittest.main()
