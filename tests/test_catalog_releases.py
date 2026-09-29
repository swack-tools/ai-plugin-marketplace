import hashlib
import io
import json
import unittest
import zipfile
from scripts.catalog.models import CatalogError


def package(path, version='1.0.0', name='vale', extra=None):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        z.writestr(path,json.dumps({'name':name,'version':version}))
        z.writestr(('vale/' if path.startswith('vale/') else '')+'skills/check/SKILL.md','---\nname: check\n---\nHello')
        if extra: z.writestr(extra,json.dumps({'name':'other','version':version}))
    return out.getvalue()

class ReleaseTests(unittest.TestCase):
    def test_accepts_portable_and_legacy_codex_archives(self):
        from scripts.catalog.releases import verify_package
        for path in ['plugin.json','.codex-plugin/plugin.json']:
            data=package(path)
            self.assertEqual(verify_package(data,hashlib.sha256(data).hexdigest(),'vale','v1.0.0','codex')['manifest_path'],path)

    def test_accepts_matching_portable_and_compatibility_identity(self):
        from scripts.catalog.releases import verify_package
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w') as z:
            for path in ['token-max/plugin.json','token-max/.codex-plugin/plugin.json']:
                z.writestr(path,json.dumps({'name':'token-max','version':'0.4.0'}))
        data=output.getvalue()
        self.assertEqual(verify_package(data,hashlib.sha256(data).hexdigest(),'token-max','v0.4.0','codex')['manifest_path'],'token-max/plugin.json')

    def test_accepts_one_plugin_named_wrapper(self):
        from scripts.catalog.releases import verify_package
        data=package('vale/.claude-plugin/plugin.json')
        self.assertEqual(verify_package(data,hashlib.sha256(data).hexdigest(),'vale','v1.0.0','claude')['manifest_path'],'vale/.claude-plugin/plugin.json')

    def test_rejects_wrong_checksum_identity_version_and_conflicts(self):
        from scripts.catalog.releases import verify_package
        for data,digest in [(package('plugin.json'), '0'*64),(package('plugin.json',version='0.1.0'),None),(package('plugin.json',name='other'),None),(package('plugin.json',extra='.codex-plugin/plugin.json'),None),(b'broken',None)]:
            with self.subTest(digest=digest), self.assertRaises(CatalogError):
                verify_package(data,digest or hashlib.sha256(data).hexdigest(),'vale','v1.0.0','codex')

    def test_newest_complete_release_keeps_older_pair(self):
        from scripts.catalog.releases import complete_releases
        assets={'claude':'c.zip','codex':'x.zip','checksums':'SHA256SUMS'}
        def release(tag,names,**kw): return dict(tag_name=tag,assets=[{'name':n} for n in names],published_at=tag,draft=False,prerelease=False,**kw)
        records=[release('v3',['c.zip']),release('v2',[*assets.values(),'other.txt']),release('v1',list(assets.values()))]
        self.assertEqual([r['tag_name'] for r in complete_releases(records,assets)], ['v2','v1'])
        self.assertEqual(complete_releases([],assets),[])
