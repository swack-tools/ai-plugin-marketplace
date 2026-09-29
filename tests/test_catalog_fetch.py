import io
import unittest
import zipfile

class FetchTests(unittest.TestCase):
    def test_archive_collection_rejects_escape_and_duplicates(self):
        from scripts.catalog.fetch import archive_files
        from scripts.catalog.models import CatalogError
        for names in [['root/../../escape.md'], ['root/a.md','root/a.md'], ['root/a.md','other/b.md']]:
            stream = io.BytesIO()
            with zipfile.ZipFile(stream,'w') as z:
                for name in names: z.writestr(name,'data')
            with self.assertRaises(CatalogError): archive_files(stream.getvalue(), strip_root=True)

    def test_archive_collection_skips_symlinks(self):
        from scripts.catalog.fetch import archive_files
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            z.writestr('root/README.md','Hello')
            link=zipfile.ZipInfo('root/link.md');link.external_attr=0o120777 << 16
            z.writestr(link,'README.md')
        self.assertEqual(archive_files(stream.getvalue(),strip_root=True), {'README.md':b'Hello'})

    def test_unapproved_network_target_is_rejected(self):
        from scripts.catalog.fetch import GitHubClient
        from scripts.catalog.models import CatalogError
        for url in ['http://api.github.com/x','https://example.com/x','https://api.github.com@evil.com/x']:
            with self.assertRaises(CatalogError): GitHubClient().get(url)

    def test_source_lock_replays_pinned_input_and_checks_digest(self):
        import json
        import tempfile
        from pathlib import Path
        from scripts.catalog.fetch import write_source_lock,load_locked_snapshot
        from scripts.catalog.models import SourceSnapshot,load_registry,CatalogError
        config=load_registry(Path('catalog/projects.json'))[0]
        snapshot=SourceSnapshot(config.id,config.repo,'a'*40,'2026-01-01',{'README.md':b'Hello'},[{'id':1,'tag_name':'v1.0.0','draft':False,'prerelease':False,'published_at':'2026-01-01','body':'Notes','html_url':'https://example.com','assets':[]}])
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:z.writestr('root/README.md','Hello')
        class Client:
            def get(self,url):
                self.url=url
                return stream.getvalue()
        client=Client()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'sources.lock.json'
            write_source_lock([snapshot],{config.id:None},path)
            entry=json.loads(path.read_text())['sources'][0]
            replay=load_locked_snapshot(config,entry,client)
            self.assertEqual(replay.files,snapshot.files)
            self.assertEqual(replay.release_candidates,snapshot.release_candidates)
            self.assertTrue(client.url.endswith('a'*40))
            entry['files']['README.md']='0'*64
            with self.assertRaisesRegex(CatalogError,'Locked source digest'):
                load_locked_snapshot(config,entry,client)
