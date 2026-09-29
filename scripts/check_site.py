"""Check static output structure, relative links, and public content."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
try:
    from scripts.catalog.render import PRIVATE
except ModuleNotFoundError:
    from catalog.render import PRIVATE


def check_site(output,catalog):
    output=Path(output);errors=[]
    for path in output.rglob('*'):
        if not path.is_file(): continue
        relative=path.relative_to(output).as_posix()
        if path.suffix not in ('.html','.json','.css','.js','.svg','.xml') and path.name not in ('CNAME','.nojekyll'):
            errors.append(f'Unexpected public file: {relative}')
        text=path.read_text()
        if PRIVATE.search(text): errors.append(f'Private data pattern: {relative}')
        if path.suffix!='.html':continue
        soup=BeautifulSoup(text,'html.parser')
        if not soup.select_one('html[lang=en]') or not soup.select_one('main') or len(soup.select('h1'))!=1: errors.append(f'Invalid landmarks: {relative}')
        ids=[tag['id'] for tag in soup.select('[id]')]
        if len(ids)!=len(set(ids)):errors.append(f'duplicate ID: {relative}')
        for tag in soup.select('a[href],link[href],script[src],img[src]'):
            value=tag.get('href',tag.get('src'));parts=urlsplit(value)
            if parts.scheme:
                if parts.scheme not in ('https','http'):errors.append(f'Unsafe URL: {relative}')
                if re.search(r'github.com/swack-tools/(vale|trakt|token-max)-ai-plugin/(blob|tree)/',value) and not re.search(r'/(blob|tree)/[0-9a-f]{40}(?:/|$)',value):errors.append(f'Unpinned source: {relative}')
                continue
            if value.startswith('/') or '\\' in value:errors.append(f'Nonrelative site URL: {relative}');continue
            target=(path.parent/unquote(parts.path)).resolve() if parts.path else path.resolve()
            if not target.is_relative_to(output.resolve()) or not target.is_file():errors.append(f'Broken local link: {relative} -> {parts.path}');continue
            if parts.fragment and target.suffix=='.html':
                linked=BeautifulSoup(target.read_text(),'html.parser')
                if linked.find(id=unquote(parts.fragment)) is None:errors.append(f'Broken anchor: {relative} -> {parts.fragment}')
    for p in catalog['projects']:
        page=output/'plugins'/p['id']/'index.html'
        if not page.is_file():errors.append(f'Missing plugin page: {p["id"]}');continue
        text=page.read_text()
        for cap in p['capabilities']:
            if not cap['examples']:errors.append(f'Missing example: {cap["id"]}')
            for example in cap['examples']:
                if not example['input_or_trigger']:errors.append(f'Empty example: {cap["id"]}')
        if p['release']:
            for asset in p['release']['assets'].values():
                if asset['url'] not in text:errors.append(f'Missing release link: {p["id"]}')
    return errors


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--site',type=Path,required=True);parser.add_argument('--catalog',type=Path,required=True);args=parser.parse_args()
    errors=check_site(args.site,json.loads(args.catalog.read_text()))
    for error in errors: print(error)
    print(f'Site checks: {len(errors)} errors')
    raise SystemExit(bool(errors))
