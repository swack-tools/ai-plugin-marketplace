import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


class MarketplaceManifestTests(unittest.TestCase):
    def test_client_manifests_point_at_catalog_plugin_roots(self):
        expected = {
            project['id']: (
                f"https://github.com/{project['repo']}.git",
                project['plugin_root'],
                project['ref'],
            )
            for project in load('catalog/projects.json')['projects']
        }
        for path in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
            with self.subTest(path=path):
                plugins = load(path)['plugins']
                # Codex silently drops entries with a source type it does not recognize.
                self.assertEqual({plugin['source']['source'] for plugin in plugins}, {'git-subdir'})
                actual = {
                    plugin['name']: (
                        plugin['source']['url'],
                        plugin['source']['path'],
                        plugin['source']['ref'],
                    )
                    for plugin in plugins
                }
                self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
