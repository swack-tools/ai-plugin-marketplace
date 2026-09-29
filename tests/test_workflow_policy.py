import re
import unittest
from pathlib import Path
import yaml

class WorkflowTests(unittest.TestCase):
    def test_only_main_publish_events_can_deploy(self):
        data=yaml.safe_load(Path('.github/workflows/pages.yml').read_text())
        jobs=data['jobs']
        self.assertIn('deploy',jobs)
        condition=jobs['deploy']['if']
        self.assertIn("github.ref == 'refs/heads/main'",condition)
        self.assertIn("github.event_name != 'pull_request'",condition)
        self.assertEqual(jobs['build'].get('permissions',data.get('permissions')),{'contents':'read'})
        self.assertEqual(jobs['deploy']['permissions'],{'pages':'write','id-token':'write'})

    def test_actions_are_immutable_and_preview_contains_only_site(self):
        data=yaml.safe_load(Path('.github/workflows/pages.yml').read_text())
        for job in data['jobs'].values():
            for step in job['steps']:
                if 'uses' in step: self.assertRegex(step['uses'],r'@[0-9a-f]{40}$')
                if 'upload-pages-artifact' in step.get('uses',''):self.assertEqual(step['with']['path'],'build/site')
        events=data.get('on',data.get(True))
        self.assertEqual(events['push']['branches'],['main'])
        self.assertIn('schedule',events);self.assertIn('pull_request',events)
        self.assertNotIn('pull_request_target',events)
