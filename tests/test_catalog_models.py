import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

class ModelsTests(unittest.TestCase):
    def test_catalog_contract_exists(self):
        self.assertTrue(Path('scripts/catalog/models.py').exists(), 'catalog model implementation is missing')

    def test_registry_contains_exact_project_roots(self):
        from scripts.catalog.models import load_registry
        projects = load_registry(Path('catalog/projects.json'))
        self.assertEqual([(p.id, p.plugin_root) for p in projects], [('vale','plugins/vale'), ('trakt-mcp','plugins/trakt-mcp'), ('token-max','plugins/token-max')])

    def test_rejects_absolute_or_parent_paths(self):
        from scripts.catalog.models import relative_path, CatalogError
        for value in ['/tmp/x', '../x', 'a/../../x', 'C:\\x', 'a\\x', '', 'https://x']:
            with self.subTest(value=value), self.assertRaises(CatalogError):
                relative_path(value)

    def test_serialization_is_stable(self):
        from scripts.catalog.models import serialize_catalog
        self.assertEqual(serialize_catalog({'b':2,'a':1}), serialize_catalog({'a':1,'b':2}))

    def test_unknown_is_not_zero(self):
        from scripts.catalog.models import SourceRef, CatalogError
        with self.assertRaises(CatalogError):
            SourceRef('swack-tools/vale-ai-plugin', 'main', 'README.md')

    def test_cli_requires_one_input_mode(self):
        run = subprocess.run([sys.executable, 'scripts/build_site.py'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('--offline', run.stderr)
        self.assertIn('--live', run.stderr)
