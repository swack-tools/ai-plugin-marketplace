import tempfile
import unittest
from pathlib import Path
from scripts.catalog.models import SourceRef,CatalogError

class RenderTests(unittest.TestCase):
    def test_relative_navigation_survives_prefix(self):
        from scripts.catalog.render import page_url
        self.assertEqual(page_url('plugins/vale/index.html','assets/site.css'),'../../assets/site.css')
        self.assertEqual(page_url('index.html','plugins/vale/index.html'),'plugins/vale/index.html')

    def test_source_urls_are_pinned_and_encoded(self):
        from scripts.catalog.render import source_url
        self.assertEqual(source_url(SourceRef('swack-tools/vale-ai-plugin','a'*40,'docs/a b.md')), 'https://github.com/swack-tools/vale-ai-plugin/blob/'+('a'*40)+'/docs/a%20b.md')

    def test_render_rejects_active_html_and_unsafe_links(self):
        from scripts.catalog.render import render_content
        block={'format':'html','text':'<script>alert(1)</script><p onclick="evil()">Hello <a href="javascript:evil()">bad</a><a href="README.md">read</a></p>','source':{'repo':'swack-tools/vale-ai-plugin','commit':'a'*40,'path':'docs/index.html'},'links':{'README.md':'https://github.com/swack-tools/vale-ai-plugin/blob/'+('a'*40)+'/docs/README.md'}}
        html=render_content(block)
        self.assertNotIn('script',html);self.assertNotIn('onclick',html);self.assertNotIn('javascript:',html)
        self.assertIn('/blob/'+('a'*40)+'/docs/README.md',html)

    def test_imported_branch_links_use_the_source_commit(self):
        from scripts.catalog.render import render_content
        block={'format':'markdown','text':'[Guide](https://github.com/swack-tools/vale-ai-plugin/blob/main/docs/usage.md)','source':{'repo':'swack-tools/vale-ai-plugin','commit':'a'*40,'path':'README.md'},'links':{'https://github.com/swack-tools/vale-ai-plugin/blob/main/docs/usage.md':'https://github.com/swack-tools/vale-ai-plugin/blob/'+('a'*40)+'/docs/usage.md'}}
        html=render_content(block)
        self.assertIn('/blob/'+('a'*40)+'/docs/usage.md',html)
        self.assertNotIn('/blob/main/',html)

    def test_public_https_url_is_not_a_windows_path(self):
        from scripts.catalog.render import PRIVATE
        self.assertIsNone(PRIVATE.search('https://github.com/swack-tools'))

    def test_private_paths_do_not_enter_public_html(self):
        from scripts.catalog.render import render_content
        # Synthetic privacy canary assembled without committing a user's real path.
        block={'format':'markdown','text':'```sh\ncat '+chr(47)+'Users/example/private.txt\n```','source':{'repo':'swack-tools/vale-ai-plugin','commit':'a'*40,'path':'README.md'}}
        html=render_content(block)
        self.assertNotIn('private.txt',html)
        self.assertIn('source',html.lower())

    def test_imported_website_routes_resolve_to_existing_sources(self):
        from scripts.catalog.documents import source_links
        from scripts.catalog.models import SourceSnapshot
        snapshot=SourceSnapshot('vale','swack-tools/vale-ai-plugin','a'*40,'2026-01-01',{'docs/index.md':b'Overview','docs/installation.md':b'Install'})
        links=source_links(snapshot,{'source':{'path':'docs/index.md'},'format':'markdown','text':'[Install](installation.html)'})
        self.assertTrue(links['installation.html'].endswith('/docs/installation.md'))
        with self.assertRaisesRegex(CatalogError,'Linked source missing'):
            source_links(snapshot,{'source':{'path':'docs/index.md'},'format':'markdown','text':'[Missing](missing.html)'})
