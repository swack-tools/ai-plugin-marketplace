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
