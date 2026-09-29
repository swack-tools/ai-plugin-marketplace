"""Select complete stable releases and validate client packages."""
import hashlib
import json
import re
from urllib.parse import quote
from .fetch import archive_files, approved_url
from .models import CatalogError, VerifiedRelease


def verify_package(data, digest, plugin_id, tag, client):
    if hashlib.sha256(data).hexdigest()!=digest:
        raise CatalogError('Release checksum mismatch')
    files=archive_files(data)
    paths=['.claude-plugin/plugin.json'] if client=='claude' else ['plugin.json','.codex-plugin/plugin.json']
    manifests=[p for p in paths if p in files]
    if len(manifests)!=1: raise CatalogError('Package must contain exactly one client manifest')
    manifest=json.loads(files[manifests[0]])
    if manifest.get('name')!=plugin_id or manifest.get('version')!=tag.removeprefix('v'):
        raise CatalogError('Release tag and plugin identity/version disagree')
    return {'sha256':digest,'manifest_path':manifests[0],'version':manifest['version']}


def complete_releases(records, names):
    result=[]
    for release in records:
        if release['draft'] or release['prerelease']: continue
        assets=[a['name'] for a in release['assets']]
        if all(assets.count(n)==1 for n in names.values()): result.append(release)
    return sorted(result,key=lambda r:r['published_at'],reverse=True)


def select_release(config, records, client):
    candidates=complete_releases(records,config.release_assets)
    if not candidates: return None
    release=candidates[0]
    tag=release['tag_name']
    if not re.fullmatch(r'v?\d+\.\d+\.\d+(?:\+[\w.-]+)?',tag):
        raise CatalogError('Unsupported stable release tag')
    def tag_commit():
        return client.api(f'repos/{config.repo}/commits/{quote(tag,safe="")}')['sha']
    commit=tag_commit()
    assets={a['name']:a for a in release['assets']}
    def download(name):
        asset=assets[name]
        url=asset['browser_download_url']
        prefix=f'https://github.com/{config.repo}/releases/download/{quote(tag,safe="")}/'
        if not url.startswith(prefix) or url[len(prefix):]!=quote(name):
            raise CatalogError('Unexpected release asset URL')
        return client.get(url)
    checksums={}
    for line in download(config.release_assets['checksums']).decode().splitlines():
        match=re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?([^/\\]+)',line)
        if not match or match[2] in checksums: raise CatalogError('Invalid checksum manifest')
        checksums[match[2]]=match[1].lower()
    verified={}
    for target in ('claude','codex'):
        name=config.release_assets[target]
        if name not in checksums: raise CatalogError('Missing release checksum')
        entry=verify_package(download(name),checksums[name],config.id,tag,target)
        entry.update(url=assets[name]['browser_download_url'],id=assets[name]['id'],name=name)
        verified[target]=entry
    current=client.api(f'repos/{config.repo}/releases/{release["id"]}')
    identity=lambda r: sorted((a['id'],a['name'],a['size'],a['updated_at']) for a in r['assets'])
    if current.get('draft') or current.get('prerelease') or current['tag_name']!=tag or identity(current)!=identity(release) or tag_commit()!=commit:
        raise CatalogError('Release changed during verification')
    return VerifiedRelease(tag,commit,release['html_url'],release['published_at'],verified)
