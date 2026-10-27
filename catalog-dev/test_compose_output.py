"""Private output preserves executable strings/secrets and enforces API headroom."""
import json
import unittest
import yaml
from compose_output import compact_document, dump_private_compose


class OutputTests(unittest.TestCase):
    def test_literal_scripts_and_credentials_roundtrip_with_only_unused_configs_removed(self):
        source={'services':{'worker':{'image':'repo:tag','environment':{'PASSWORD':'example$secret\\literal'},
            'configs':[{'source':'script','target':'/catalog/test.py'}]}},
            'configs':{'script':{'content':"print('literal\\n')\nvalue = '$$keep'\n"},
                'obsolete':{'content':'unused'}}}
        result=dump_private_compose(source)
        self.assertEqual(yaml.safe_load(result),compact_document(source))
        self.assertIn('obsolete',source['configs'])
        self.assertIn('content: |',result)
        self.assertLess(len(json.dumps(result.replace('\n','\r\n'))),60*1024)

    def test_string_config_mounts_are_kept(self):
        source={'services':{'worker':{'configs':['script']}},'configs':{'script':{'content':'data'}}}
        self.assertEqual(yaml.safe_load(dump_private_compose(source)),source)

    def test_oversized_output_is_refused(self):
        with self.assertRaisesRegex(ValueError,'request budget'):
            dump_private_compose({'services':{'worker':{'environment':{'TOO_BIG':'a'*62000}}}})

    def test_repeated_blocks_use_anchors_without_changing_service_values(self):
        source={'services':{f'worker-{index}':{'image':'example:tag',
            'environment':{'REPEATED':'same value '*80},'volumes':[{'type':'bind','source':'/mnt/lab/sites','target':'/sites'}]}
            for index in range(20)}}
        result=dump_private_compose(source)
        self.assertEqual(yaml.safe_load(result),source)
        self.assertIn('&id',result)
        self.assertLess(len(result),len(yaml.safe_dump(source))//2)


if __name__=='__main__': unittest.main()
