"""Bounded GitHub reads. Collected repository code is never executed."""
import io
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from .models import CatalogError, SourceSnapshot, relative_path, serialize_catalog

MAX_DOWNLOAD = 100 * 1024 * 1024
MAX_EXPANDED = 250 * 1024 * 1024
MAX_TEXT = 2 * 1024 * 1024
HOSTS = {'api.github.com','github.com','codeload.github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'}


def approved_url(url):
    value = urllib.parse.urlsplit(url)
    if value.scheme != 'https' or value.hostname not in HOSTS or value.username or value.password or value.port not in (None,443):
        raise CatalogError('Unapproved download URL')
    return url


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        approved_url(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if urllib.parse.urlsplit(newurl).hostname != urllib.parse.urlsplit(req.full_url).hostname:
            redirected.remove_header('Authorization')
        return redirected


class GitHubClient:
    def __init__(self, token=None):
        self.token = token or os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        self.opener = urllib.request.build_opener(SafeRedirect())

    def get(self, url):
        approved_url(url)
        headers = {'User-Agent':'swack-tools-catalog','Accept':'application/vnd.github+json'}
        if self.token and urllib.parse.urlsplit(url).hostname == 'api.github.com':
            headers['Authorization'] = f'Bearer {self.token}'
        for attempt in range(3):
            try:
                with self.opener.open(urllib.request.Request(url,headers=headers),timeout=30) as response:
                    data = response.read(MAX_DOWNLOAD+1)
                    if len(data)>MAX_DOWNLOAD:
                        raise CatalogError('Download exceeds size limit')
                    return data
            except urllib.error.HTTPError as exc:
                if exc.code not in (429,500,502,503,504) or attempt == 2:
                    raise CatalogError(f'GitHub request failed (HTTP {exc.code})') from None
            except (urllib.error.URLError,TimeoutError):
                if attempt == 2:
                    raise CatalogError('GitHub request timed out or failed') from None
            time.sleep(attempt+1)

    def api(self, path):
        return json.loads(self.get('https://api.github.com/'+path))

    def releases(self, repo):
        records=[]
        for page in range(1,101):
            batch=self.api(f'repos/{repo}/releases?per_page=100&page={page}')
            records.extend(batch)
            if len(batch)<100: return records
        raise CatalogError('Release pagination exceeds supported limit')


def archive_files(data: bytes, strip_root=False):
    if len(data)>MAX_DOWNLOAD: raise CatalogError('Archive exceeds size limit')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries=archive.infolist()
            if len(entries)>5000 or sum(i.file_size for i in entries)>MAX_EXPANDED:
                raise CatalogError('Archive expansion exceeds size limit')
            files={}; seen=set(); root=None
            for item in entries:
                path=relative_path(item.filename.rstrip('/'))
                if strip_root:
                    first,_,path=path.partition('/')
                    if root is not None and first!=root: raise CatalogError('Archive has multiple roots')
                    root=first
                    if not path: continue
                if item.is_dir(): continue
                path=relative_path(path)
                if path in seen: raise CatalogError('Duplicate archive path')
                seen.add(path)
                mode=item.external_attr >> 16
                if stat.S_ISLNK(mode): continue
                # CRC is verified when each member is read, including unparsed binary files.
                content=archive.read(item)
                if len(content)<=MAX_TEXT: files[path]=content
                elif Path(path).suffix.lower() in ('.md','.json','.html','.yaml','.yml','.py','.rs','.ts'):
                    raise CatalogError(f'Parsed file exceeds size limit: {path}')
            return files
    except (zipfile.BadZipFile, RuntimeError, OSError):
        raise CatalogError('Invalid or corrupt ZIP archive') from None


def collect_snapshot(config, cache: Path, client: GitHubClient):
    metadata=client.api(f'repos/{config.repo}/commits/{urllib.parse.quote(config.ref,safe="")}')
    sha=metadata['sha']
    if not re.fullmatch('[0-9a-f]{40}',sha): raise CatalogError('Invalid resolved source SHA')
    location=cache/config.id/(sha+'.zip')
    if location.exists():
        data=location.read_bytes()
    else:
        data=client.get(f'https://api.github.com/repos/{config.repo}/zipball/{sha}')
        archive_files(data,strip_root=True)
        location.parent.mkdir(parents=True,exist_ok=True)
        location.write_bytes(data)
    return SourceSnapshot(config.id,config.repo,sha,metadata['commit']['committer']['date'],archive_files(data,strip_root=True),client.releases(config.repo))


def write_source_lock(snapshots, releases, path):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=('id','tag_name','draft','prerelease','published_at','body','html_url')
    asset_fields=('id','name','size','updated_at','browser_download_url')
    sources=[]
    for snapshot in snapshots:
        candidates=[{**{k:r.get(k) for k in fields},'assets':[{k:a[k] for k in asset_fields} for a in r['assets']]} for r in snapshot.release_candidates]
        sources.append({'id':snapshot.project_id,'repo':snapshot.repo,'commit':snapshot.commit,'date':snapshot.commit_date,'files':{p:hashlib.sha256(data).hexdigest() for p,data in snapshot.files.items()},'release_candidates':candidates,'release':releases[snapshot.project_id]})
    path.write_bytes(serialize_catalog({'schema_version':1,'sources':sources}))


def load_locked_snapshot(config,entry,client):
    from .models import SourceRef
    if entry['id']!=config.id or entry['repo']!=config.repo: raise CatalogError('Locked repository mismatch')
    SourceRef(config.repo,entry['commit'],'README.md')
    data=client.get(f'https://api.github.com/repos/{config.repo}/zipball/{entry["commit"]}')
    files=archive_files(data,strip_root=True)
    if {p:hashlib.sha256(data).hexdigest() for p,data in files.items()}!=entry['files']:
        raise CatalogError('Locked source digest mismatch')
    return SourceSnapshot(config.id,config.repo,entry['commit'],entry['date'],files,entry['release_candidates'])


def load_snapshot(config,directory):
    base=Path(directory)/config.id
    metadata=json.loads((base/'snapshot.json').read_text())
    files={p.relative_to(base).as_posix():p.read_bytes() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and p.name!='snapshot.json'}
    from .models import SourceRef
    SourceRef(config.repo,metadata['commit'],'README.md')
    return SourceSnapshot(config.id,config.repo,metadata['commit'],metadata['commit_date'],files,metadata.get('release_candidates',[])),metadata.get('release')
