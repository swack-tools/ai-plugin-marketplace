"""Render safe static pages with relative navigation."""
from dataclasses import asdict, is_dataclass
import json
import posixpath
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit, urljoin, quote
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup
from markdown_it import MarkdownIt
import nh3
from .models import CatalogError, SourceRef, serialize_catalog

PRIVATE = re.compile(r'/(?:Users|home)/[^\s<]+|(?<![A-Za-z])[A-Za-z]:[\\/]|\\\\[A-Za-z]|file://|(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{15,}|fc-[a-f0-9]{25,}')
TAGS={'p','br','strong','em','code','pre','ul','ol','li','blockquote','a','table','thead','tbody','tr','th','td','h2','h3','h4','details','summary','span','div'}


def source_url(ref):
    return (SourceRef(**ref) if isinstance(ref,dict) else ref).url


def page_url(from_page,to_page):
    return posixpath.relpath(to_page,posixpath.dirname(from_page) or '.')


def render_content(block,context=None):
    text=block['text']
    html=MarkdownIt('commonmark',{'html':False}).enable('table').render(text) if block['format']=='markdown' else text
    soup=BeautifulSoup(html,'html.parser')
    for tag in soup.select('script,style,iframe,form,img,svg,input,button'): tag.decompose()
    for tag in list(soup.select('pre,p,li,td,th')):
        if tag.parent is not None and PRIVATE.search(tag.get_text()):
            tag.clear();tag.append('See the source for this example.')
    if PRIVATE.search(soup.get_text()): return Markup('<p>See the source for this section.</p>')
    ref=block.get('source')
    for a in soup.select('a[href]'):
        href=a['href'];parts=urlsplit(href)
        if href in block.get('links',{}):
            a['href']=block['links'][href];continue
        if ref and href.startswith(f'https://github.com/{ref["repo"]}/blob/'):
            raise CatalogError('Imported source link was not validated')
        if parts.scheme:
            if parts.scheme not in ('https','http') or parts.username or parts.password: a.unwrap()
            continue
        if href.startswith('//') or '\\' in href: a.unwrap();continue
        if ref:
            raise CatalogError('Imported source link was not validated')
        elif block.get('release_url'):
            a['href']=urljoin(block['release_url'],href)
        else: a.unwrap()
    # Imported IDs/headings cannot collide with the shared page structure.
    for h in soup.select('h1,h2,h3,h4,h5,h6'):
        h.name='p';h.wrap(soup.new_tag('strong'))
    clean=nh3.clean(str(soup),tags=TAGS,attributes={'a':{'href','title'},'th':{'scope'}},url_schemes={'https','http'},link_rel='noopener noreferrer')
    return Markup(clean)


def render_site(catalog,templates,assets,content,output):
    if is_dataclass(catalog):catalog=asdict(catalog)
    catalog=json.loads(serialize_catalog(catalog))
    output=Path(output)
    if output.is_symlink(): raise CatalogError('Output cannot be a symlink')
    output.mkdir(parents=True,exist_ok=True)
    env=Environment(loader=FileSystemLoader(templates),autoescape=select_autoescape(['html']),undefined=StrictUndefined)
    env.globals.update(source_url=source_url,content=render_content)
    env.tests['contains'] = lambda values, value: value in values
    env.filters['invocation_request'] = lambda text: re.sub(r'^(?:/[a-z0-9-]+:[a-z0-9-]+|\$[a-z0-9-]+)\s+', '', text)
    projects=catalog['projects']
    pages=[('index.html','overview.html',None),('install/index.html','install.html',None),('404.html','404.html',None)]+[(f'plugins/{p["id"]}/index.html','plugin.html',p) for p in projects]
    for route,template,project in pages:
        target=output/route;target.parent.mkdir(parents=True,exist_ok=True)
        context={'projects':projects,'project':project,'route':route,'url':lambda path:page_url(route,path),'domain':'https://ai.swacktech.com/','catalog_commit':catalog.get('marketplace_commit','a'*40)}
        if route=='install/index.html':context['installation']={'text':(content/'install.md').read_text(),'format':'markdown'}
        html=env.get_template(template).render(**context)
        if PRIVATE.search(html): raise CatalogError('Private path or credential pattern in rendered page')
        target.write_text(html)
    shutil.copytree(assets,output/'assets',dirs_exist_ok=True)
    (output/'.nojekyll').write_text('')
    (output/'CNAME').write_text('ai.swacktech.com\n')
    (output/'catalog.json').write_bytes(serialize_catalog(catalog))
    (output/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>https://ai.swacktech.com/'+r+'</loc></url>' for r,_,_ in pages if r!='404.html')+'</urlset>')
    return [output/r for r,_,_ in pages]
