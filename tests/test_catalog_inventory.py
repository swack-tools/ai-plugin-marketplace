import json
import unittest
from scripts.catalog.models import load_registry, SourceSnapshot, CatalogError
from pathlib import Path


def sample(files):
    return SourceSnapshot('vale','swack-tools/vale-ai-plugin','a'*40,'2026-01-01', {k:(v.encode() if isinstance(v,str) else v) for k,v in files.items()})

class InventoryTests(unittest.TestCase):
    def setUp(self): self.config=load_registry(Path('catalog/projects.json'))[0]

    def test_custom_skills_add_to_default_and_preserve_flags(self):
        from scripts.catalog.inventory import inventory_plugin, capability_counts
        s=sample({'plugins/vale/.claude-plugin/plugin.json':json.dumps({'name':'vale','skills':['./extra/']}), 'plugins/vale/skills/a/SKILL.md':'---\nname: a\ndescription: >\n  A multiline\n  description.\n---\nA', 'plugins/vale/extra/b/SKILL.md':'---\nname: b\ndescription: B\nuser-invocable: false\n---\nB'})
        items,_=inventory_plugin(self.config,s)
        self.assertEqual(capability_counts(items)['skills'],2)
        self.assertEqual(items[0].description,'A multiline description.\n')
        self.assertFalse(items[1].details['user_invocable'])

    def test_explicit_missing_and_escape_paths_are_errors(self):
        from scripts.catalog.inventory import inventory_plugin
        for path in ['./missing','../escape']:
            s=sample({'plugins/vale/.claude-plugin/plugin.json':json.dumps({'name':'vale','skills':path})})
            with self.assertRaises(CatalogError): inventory_plugin(self.config,s)

    def test_duplicate_skill_names_fail(self):
        from scripts.catalog.inventory import inventory_plugin
        s=sample({'plugins/vale/.claude-plugin/plugin.json':'{"name":"vale"}',**{f'plugins/vale/skills/{x}/SKILL.md':'---\nname: same\ndescription: A\n---\nA' for x in ('a','b')}})
        with self.assertRaises(CatalogError): inventory_plugin(self.config,s)

    def test_mcp_mirrors_deduplicate_without_secrets(self):
        from scripts.catalog.inventory import inventory_plugin,capability_counts
        m=json.dumps({'mcpServers':{'example':{'type':'http','url':'https://example.com/mcp','headers':{'Authorization':'SECRET'}}}})
        s=sample({'plugins/vale/plugin.json':'{"name":"vale"}', 'plugins/vale/.claude-plugin/plugin.json':'{"name":"vale"}', 'plugins/vale/mcp.json':m,'plugins/vale/.mcp.json':m})
        items,_=inventory_plugin(self.config,s)
        self.assertEqual(capability_counts(items)['mcp_servers'],1)
        self.assertNotIn('SECRET',repr(items))
        self.assertEqual(items[0].clients,['claude','codex'])

    def test_hook_actions_are_counted_separately(self):
        from scripts.catalog.inventory import inventory_plugin,capability_counts
        s=sample({'plugins/vale/.claude-plugin/plugin.json':'{"name":"vale"}','plugins/vale/hooks/hooks.json':json.dumps({'hooks':{'Stop':[{'hooks':[{'type':'command','command':'echo a'},{'type':'command','command':'echo b'}]}]}})})
        counts=capability_counts(inventory_plugin(self.config,s)[0])
        self.assertEqual((counts['hook_actions'],counts['hook_events']),(2,1))

    def test_different_client_hook_handlers_are_rejected(self):
        from scripts.catalog.inventory import inventory_plugin
        files={'plugins/vale/.claude-plugin/plugin.json':json.dumps({'name':'vale','hooks':{'hooks':{'Stop':[{'hooks':[{'type':'command','command':'echo first'}]}]}}}), 'plugins/vale/plugin.json':json.dumps({'name':'vale','extensions':{'com.openai':{'hooks':{'hooks':{'Stop':[{'hooks':[{'type':'command','command':'echo second'}]}]}}}}})}
        with self.assertRaisesRegex(CatalogError,'Conflicting hook handlers'):
            inventory_plugin(self.config,sample(files))

    def test_explicit_empty_component_targets_are_rejected(self):
        from scripts.catalog.inventory import inventory_plugin
        for path in ['./README.md','./extra']:
            files={'plugins/vale/.claude-plugin/plugin.json':json.dumps({'name':'vale','skills':path}), 'plugins/vale/README.md':'Not a skill', 'plugins/vale/extra/README.md':'No definitions'}
            with self.assertRaisesRegex(CatalogError,'No supported skills'):
                inventory_plugin(self.config,sample(files))
