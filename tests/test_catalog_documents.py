import copy
import unittest
from scripts.catalog.models import SourceSnapshot,Capability,CatalogError

def snapshot(files):
    return SourceSnapshot('vale','swack-tools/vale-ai-plugin','a'*40,'2026-01-01',{k:v.encode() for k,v in files.items()})

class DocumentTests(unittest.TestCase):
    def test_reviewed_prose_edit_preserves_source_and_detects_drift(self):
        from scripts.catalog.documents import apply_prose_edits
        import hashlib
        source=snapshot({'README.md':'Docs, tools and examples.'})
        edits=[{'path':'README.md','sha256':hashlib.sha256(source.files['README.md']).hexdigest(),'before':'tools and examples','after':'tools, and examples'}]
        self.assertEqual(apply_prose_edits('Docs, tools and examples.',source,'README.md',edits),'Docs, tools, and examples.')
        source.files['README.md']=b'Changed source'
        with self.assertRaises(CatalogError):apply_prose_edits('Docs, tools and examples.',source,'README.md',edits)

    def test_heading_selection_respects_hierarchy_and_fenced_code(self):
        from scripts.catalog.documents import select_document
        s=snapshot({'README.md':'# Project\n\nIntro\n\n## Use\n\nDo this.\n\n```sh\n# Not a heading\n```\n\n### Detail\nMore.\n\n## End\nStop.'})
        selected=select_document(s,{'path':'README.md','format':'markdown','mode':'section','heading_path':['Use']})
        self.assertIn('Not a heading',selected['text']);self.assertIn('More.',selected['text']);self.assertNotIn('Stop.',selected['text'])

    def test_ambiguous_or_missing_selectors_fail(self):
        from scripts.catalog.documents import select_document
        s=snapshot({'README.md':'# A\n## Use\nOne\n# B\n## Use\nTwo','page.html':'<p class="lead">One</p><p class="lead">Two</p>'})
        for selector in [{'path':'README.md','format':'markdown','mode':'section','heading_path':['Use']},{'path':'page.html','format':'html','selector':'.lead'}]:
            with self.assertRaises(CatalogError): select_document(s,selector)

    def test_coverage_requires_examples_for_each_capability(self):
        from scripts.catalog.documents import validate_example_coverage
        cap=Capability('skill:check','skill','check','Check',[],['claude'])
        self.assertTrue(validate_example_coverage([cap]))
        cap.examples=[{'input_or_trigger':'Check README.md','expected_behavior':'Report findings','prerequisites':['Install Vale'],'sources':[{'path':'README.md'}]}]
        self.assertEqual(validate_example_coverage([cap]),[])

    def test_legacy_example_is_normalized_without_guessing(self):
        from scripts.catalog.documents import normalize_example
        value=normalize_example({'title':'Check','prompt':'Check docs','platform':'claude','source':{'path':'README.md'}})
        self.assertEqual(value['input_or_trigger'],'Check docs')
        self.assertEqual(value['sources'],[{'path':'README.md'}])
        self.assertNotIn('capability_refs',value)

    def test_metadata_rejects_extra_counts_and_fake_capabilities(self):
        from scripts.catalog.documents import load_upstream_info
        import json
        for value in [{'schemaVersion':1,'pluginId':'vale','counts':{'skills':99}}, {'schemaVersion':1,'pluginId':'vale','mcpServers':{'invented':{'description':'No'}}}]:
            with self.assertRaises(CatalogError): load_upstream_info(snapshot({'catalog-info.json':json.dumps(value)}),[])

    def test_missing_changelog_uses_release_notes_without_commit_log(self):
        from scripts.catalog.documents import recent_changes
        s=snapshot({'README.md':'# A'})
        self.assertEqual(recent_changes(s,[]),[])
        result=recent_changes(s,[{'draft':False,'prerelease':False,'tag_name':'v1.0.0','body':'New feature','html_url':'https://github.com/swack-tools/vale-ai-plugin/releases/tag/v1.0.0','published_at':'2026-01-01'}])
        self.assertEqual(result[0]['text'],'New feature')
