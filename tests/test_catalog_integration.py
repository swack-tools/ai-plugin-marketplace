import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch
from scripts.catalog.models import load_registry,VerifiedRelease,CatalogError
from scripts.catalog.fetch import load_snapshot
from scripts.catalog.inventory import inventory_plugin,capability_counts
from scripts.catalog.documents import enrich_plugin

class IntegrationTests(unittest.TestCase):
    def test_all_fixtures_have_full_capability_example_coverage(self):
        expected={'vale':(3,0,0,3),'trakt-mcp':(7,1,15,0),'token-max':(1,0,0,0)}
        for config in load_registry(Path('catalog/projects.json')):
            snap,release=load_snapshot(config,Path('tests/fixtures/catalog'))
            caps,_=inventory_plugin(config,snap)
            record=enrich_plugin(config,snap,caps,VerifiedRelease(**release) if release else None)
            counts=capability_counts(caps)
            self.assertEqual(tuple(counts[k] for k in ('skills','mcp_servers','mcp_tools','hook_actions')),expected[config.id])
            self.assertTrue(all(c.examples for c in caps))
            self.assertTrue(all(len(s.commit)==40 for c in caps for s in c.sources))
            if config.id=='token-max':
                self.assertEqual(len(record.examples),4)
                self.assertEqual({u['platform'] for u in record.usage},{'claude-code','claude-desktop','codex','slack'})
            if config.id=='trakt-mcp':self.assertEqual(len(record.examples),23)

    def test_changed_evidence_stops_publication(self):
        config=load_registry(Path('catalog/projects.json'))[0]
        snap,_=load_snapshot(config,Path('tests/fixtures/catalog'))
        snap.files['docs/behavior.md']+=b'\nChanged behavior.\n'
        caps,_=inventory_plugin(config,snap)
        with self.assertRaisesRegex(CatalogError,'evidence changed'):enrich_plugin(config,snap,caps,None)

    def test_offline_build_cannot_connect_to_network(self):
        sys.path.insert(0,str(Path('scripts').resolve()))
        import build_site
        with tempfile.TemporaryDirectory() as temp:
            with patch('socket.socket.connect',side_effect=AssertionError('Network is forbidden')):
                with patch.object(sys,'argv',['build_site.py','--offline','tests/fixtures/catalog','--output',str(Path(temp)/'site')]):
                    self.assertEqual(build_site.main(),0)
            self.assertTrue((Path(temp)/'site/plugins/token-max/index.html').is_file())
