import json
import tempfile
import unittest
from pathlib import Path

class SiteTests(unittest.TestCase):
    def test_broken_links_and_duplicate_ids_are_errors(self):
        from scripts.check_site import check_site
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'index.html').write_text('<html lang="en"><main><h1>Title</h1><a href="missing.html">Missing</a><p id="a"></p><p id="a"></p></main></html>')
            errors=check_site(root,{'projects':[]})
            self.assertTrue(any('missing.html' in e for e in errors));self.assertTrue(any('duplicate' in e for e in errors))

    def test_render_is_deterministic_and_complete(self):
        from scripts.catalog.render import render_site
        catalog=json.loads(Path('tests/fixtures/catalog/expected.json').read_text())
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for path in (a,b):render_site(catalog,Path('site/templates'),Path('site/assets'),Path('content'),Path(path))
            files=lambda root:{p.relative_to(root).as_posix():p.read_bytes() for p in Path(root).rglob('*') if p.is_file()}
            self.assertEqual(files(a),files(b))
            self.assertEqual(len(list(Path(a).rglob('*.html'))),6)
