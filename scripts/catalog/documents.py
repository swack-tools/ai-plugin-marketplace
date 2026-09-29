"""Deterministic source selection and evidence-backed example coverage."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from .inventory import manifests, capability_counts
from .models import CatalogError, PluginRecord


def select_document(snapshot,selector):
    path=selector['path']; source=snapshot.source(path)
    text=snapshot.files[path].decode('utf-8')
    format=selector['format']
    if format=='html':
        matches=BeautifulSoup(text,'html.parser').select(selector['selector'])
        if len(matches)!=1: raise CatalogError(f'{snapshot.project_id}: ambiguous or missing selector: {path}')
        text=str(matches[0])
    elif format=='markdown':
        tokens=MarkdownIt('commonmark').enable('table').parse(text)
        headings=[]; stack=[]
        for i,token in enumerate(tokens):
            if token.type!='heading_open': continue
            level=int(token.tag[1]); title=tokens[i+1].content
            while stack and stack[-1][0]>=level: stack.pop()
            stack.append((level,title))
            headings.append((token.map[0],tokens[i+2].map[1] if tokens[i+2].map else token.map[1],level,[t for _,t in stack]))
        lines=text.splitlines()
        if selector.get('mode')=='lead':
            start=headings[0][1] if headings else 0
            end=headings[1][0] if len(headings)>1 else len(lines)
        else:
            wanted=selector.get('heading_path',[])
            matches=[h for h in headings if wanted and h[3][-len(wanted):]==wanted]
            if len(matches)!=1: raise CatalogError(f'{snapshot.project_id}: ambiguous or missing heading: {path}')
            selected=matches[0];start=selected[1]
            end=next((h[0] for h in headings if h[0]>selected[0] and h[2]<=selected[2]),len(lines))
        text='\n'.join(lines[start:end]).strip()
    else: raise CatalogError('Unsupported document format')
    if not text: raise CatalogError(f'{snapshot.project_id}: empty selected content: {path}')
    return {'text':text,'format':format,'source':asdict(source)}


def normalize_example(value):
    result=dict(value)
    if 'prompt' in result: result['input_or_trigger']=result.pop('prompt')
    if 'source' in result: result['sources']=[result.pop('source')]
    return result


def load_upstream_info(snapshot,capabilities):
    if 'catalog-info.json' not in snapshot.files: return None
    import jsonschema
    value=json.loads(snapshot.files['catalog-info.json'])
    try: jsonschema.validate(value,json.loads(Path('catalog/upstream-info.schema.json').read_text()))
    except jsonschema.ValidationError: raise CatalogError(f'{snapshot.project_id}: invalid catalog-info.json') from None
    if value['pluginId']!=snapshot.project_id: raise CatalogError('Metadata plugin ID mismatch')
    server_ids={c.name for c in capabilities if c.kind=='mcp_server'}
    if not set(value.get('mcpServers',{}))<=server_ids: raise CatalogError('Metadata names an unknown MCP server')
    for entry in value.get('examples',[]):
        refs=entry.get('capability_refs',[])
        if not set(refs)<={c.id for c in capabilities}: raise CatalogError('Example references unknown capability')
    hooks=value.get('hooks',[])
    if hooks:
        if not isinstance(hooks,list): raise CatalogError('Hook notes require explicit targets')
        targets={(s.path,s.locator) for c in capabilities if c.kind=='hook' for s in c.sources}
        for note in hooks:
            target=note.get('target',{})
            if (target.get('path'),target.get('pointer')) not in targets: raise CatalogError('Metadata names an unknown hook action')
    return value


def validate_example_coverage(capabilities):
    errors=[]
    for cap in capabilities:
        if not cap.examples: errors.append(f'{cap.id}: missing concrete example')
        for example in cap.examples:
            for field in ('input_or_trigger','expected_behavior','prerequisites','sources'):
                if not example.get(field): errors.append(f'{cap.id}: missing example {field}')
    return errors


def recent_changes(snapshot,candidates,limit=3):
    paths=[p for p in snapshot.files if re.search(r'(^|/)(changelog|changes|history)\.md$',p,re.I)]
    if paths:
        path=sorted(paths,key=lambda p:(p.count('/'),p))[0]
        text=snapshot.files[path].decode();tokens=MarkdownIt().parse(text);lines=text.splitlines();sections=[]
        heads=[(t.map[0],tokens[i+1].content) for i,t in enumerate(tokens) if t.type=='heading_open' and t.tag=='h2']
        for i,(start,title) in enumerate(heads):
            if not re.search(r'\d+\.\d+',title): continue
            end=heads[i+1][0] if i+1<len(heads) else len(lines)
            sections.append({'title':title,'format':'markdown','text':'\n'.join(lines[start+1:end]).strip(),'source':asdict(snapshot.source(path))})
        if sections: return sections[:limit]
    stable=sorted((r for r in candidates if not r['draft'] and not r['prerelease']),key=lambda r:r['published_at'],reverse=True)
    return [{'title':r['tag_name'],'format':'markdown','text':r.get('body') or 'No release notes were provided.','release_url':r['html_url']} for r in stable[:limit]]


def enrich_plugin(config,snapshot,capabilities,release,examples_path=Path('catalog/examples.json')):
    metadata=load_upstream_info(snapshot,capabilities)
    overview_selector=(metadata or {}).get('overview') or config.documents['overview']
    overview=[select_document(snapshot,overview_selector)]
    usage=[]
    if metadata and metadata.get('platforms'):
        for name,value in metadata['platforms'].items():
            sources=value.get('sources',[])
            if value['status']!='not_documented' and not sources: raise CatalogError('Platform support requires evidence')
            blocks=[select_document(snapshot,s) for s in sources]
            usage.append({'platform':name,'status':value['status'],'notes':value.get('notes',''),'blocks':blocks})
    else:
        usage.append({'platform':'Claude and Codex','status':'documented','notes':'Follow the upstream guide for client requirements.','blocks':[select_document(snapshot,config.documents['usage'])]})
        usage.append({'platform':'Slack','status':'not_documented','notes':'No plugin integration is documented.','blocks':[]})
    registry=json.loads(examples_path.read_text())
    import jsonschema
    try: jsonschema.validate(registry,json.loads(examples_path.with_suffix('.schema.json').read_text()))
    except jsonschema.ValidationError: raise CatalogError('Invalid reviewed examples catalog') from None
    reviewed=registry.get(config.id,[])
    entries=[]
    for item in (metadata or {}).get('examples',[]):
        normalized=normalize_example(item)
        # Original-format pilot entries require an explicit reviewed mapping.
        if not normalized.get('capability_refs'):
            matches=[r for r in reviewed if r.get('legacy_title')==item['title']]
            if len(matches)!=1: raise CatalogError('Legacy example needs a reviewed capability mapping')
            normalized={**matches[0],**normalized,'capability_refs':matches[0]['capability_refs']}
        entries.append(normalized)
    covered={ref for e in entries for ref in e.get('capability_refs',[])}
    entries.extend(e for e in reviewed if not set(e['capability_refs'])<=covered)
    ids={c.id:c for c in capabilities}; examples=[]; seen=set()
    for raw in entries:
        entry=normalize_example(raw)
        if entry['id'] in seen: raise CatalogError('Duplicate example ID')
        seen.add(entry['id'])
        sources=[]
        for selector in entry['sources']:
            if 'format' in selector: select_document(snapshot,selector)
            source=snapshot.source(selector['path'])
            if entry.get('evidence')=='reviewed_illustration':
                expected=entry.get('source_digests',{}).get(source.path)
                if expected!=hashlib.sha256(snapshot.files[source.path]).hexdigest(): raise CatalogError(f'{config.id}: example evidence changed: {source.path}')
            sources.append(asdict(source))
        normalized={k:entry[k] for k in ('id','title','input_or_trigger','platform','prerequisites','expected_behavior','evidence') if k in entry}
        normalized['sources']=sources
        for ref in entry['capability_refs']:
            if ref not in ids: raise CatalogError(f'{config.id}: orphan example: {ref}')
            ids[ref].examples.append(normalized)
        examples.append(normalized)
    errors=validate_example_coverage(capabilities)
    if errors: raise CatalogError(f'{config.id}: '+ '; '.join(errors))
    for cap in capabilities:
        if cap.kind in ('hook','mcp_server') and cap.examples:
            cap.description=cap.examples[0]['expected_behavior']
    source_manifest=next(iter(manifests(config,snapshot).values()))[1]
    return PluginRecord(config.id,config.name,source_manifest.get('description',''),source_manifest.get('version','Unversioned'),snapshot.commit,config.homepage,config.repo,config.accent,capabilities,capability_counts(capabilities),overview,examples,usage,recent_changes(snapshot,snapshot.release_candidates),release,[])
