"""Read native component declarations without executing plugin code."""
import json
from pathlib import PurePosixPath
import re
from urllib.parse import urlsplit
import yaml
from bs4 import BeautifulSoup
from .models import Capability, CatalogError, relative_path


def json_file(snapshot,path):
    snapshot.source(path)
    value=json.loads(snapshot.files[path])
    if not isinstance(value,dict): raise CatalogError(f'Expected an object: {path}')
    return value


def manifests(config,snapshot):
    root=config.plugin_root
    entries={}
    for client,paths in [('claude',[root+'/.claude-plugin/plugin.json']),('codex',[root+'/plugin.json',root+'/.codex-plugin/plugin.json'])]:
        found=[p for p in paths if p in snapshot.files]
        if not found: continue
        manifest=json_file(snapshot,found[0])
        if manifest.get('name')!=config.id: raise CatalogError('Plugin manifest name mismatch')
        for path in found[1:]:
            other=json_file(snapshot,path)
            if (other.get('name'),other.get('version'))!=(manifest.get('name'),manifest.get('version')):
                raise CatalogError('Conflicting native manifest identities')
        settings=manifest
        if client=='codex' and found[0].endswith('/plugin.json') and '/.codex-plugin/' not in found[0]:
            settings=manifest.get('extensions',{}).get('com.openai',{})
            if not settings and len(found)>1: settings=json_file(snapshot,found[1])
        entries[client]=(found[0],manifest,settings)
    if not entries: raise CatalogError(f'{config.id}: no supported plugin manifest')
    return entries


def component_path(root,value):
    if value in ('.','./'): return root
    return relative_path(root+'/'+relative_path(value))


def parse_manifest_paths(snapshot,config):
    result={}
    for client,(manifest_path,manifest,settings) in manifests(config,snapshot).items():
        paths={}
        for kind,default in [('skills','skills'),('commands','commands'),('hooks','hooks/hooks.json'),('mcpServers','mcp.json' if client=='codex' and manifest_path==config.plugin_root+'/plugin.json' else '.mcp.json')]:
            declaration=settings.get(kind)
            raw=[] if declaration is None else declaration if isinstance(declaration,list) else [declaration]
            if declaration is None or (client=='claude' and kind in ('skills','hooks','mcpServers')):
                raw=[{'default':default},*raw]
            selected=[]
            for value in raw:
                optional=isinstance(value,dict) and set(value)=={'default'}
                if optional: value=value['default']
                if isinstance(value,dict):
                    if kind not in ('hooks','mcpServers'): raise CatalogError(f'Unsupported {kind} declaration')
                    selected.append((manifest_path,value)); continue
                if not isinstance(value,str): raise CatalogError(f'Unsupported {kind} declaration')
                path=component_path(config.plugin_root,value)
                if not any(p==path or p.startswith(path+'/') for p in snapshot.files):
                    if optional: continue
                    raise CatalogError(f'Missing declared component: {path}')
                if kind in ('skills','commands') and not optional:
                    matches=[p for p in snapshot.files if (p==path or p.startswith(path+'/')) and (p.endswith('/SKILL.md') if kind=='skills' else p.endswith('.md'))]
                    if not matches: raise CatalogError(f'No supported {kind} in declared target: {path}')
                if (path,None) not in selected: selected.append((path,None))
            paths[kind]=selected
        result[client]=paths
    return result


def frontmatter(data,path):
    text=data.decode('utf-8')
    parts=text.split('---',2)
    if len(parts)!=3 or parts[0].strip(): raise CatalogError(f'Missing frontmatter: {path}')
    value=yaml.safe_load(parts[1])
    if not isinstance(value,dict) or not isinstance(value.get('description'),str): raise CatalogError(f'Missing component description: {path}')
    return value


def inventory_plugin(config,snapshot):
    found={}; diagnostics=[]; hook_identities={}
    def add(cap,key=None):
        key=key or cap.id
        if key in found:
            old=found[key]
            if old.details!=cap.details or old.description!=cap.description:
                raise CatalogError(f'Conflicting capability definitions: {cap.id}')
            for source in cap.sources:
                if source not in old.sources: old.sources.append(source)
            old.clients=sorted(set(old.clients+cap.clients))
        else: found[key]=cap
    for client,paths in parse_manifest_paths(snapshot,config).items():
        seen_skills={}
        for kind in ('skills','commands'):
            for base,_ in paths[kind]:
                candidates=[p for p in sorted(snapshot.files) if (p==base or p.startswith(base+'/')) and ((kind=='skills' and p.endswith('/SKILL.md')) or (kind=='commands' and p.endswith('.md')))]
                for path in candidates:
                    data=frontmatter(snapshot.files[path],path)
                    name=data.get('name') or PurePosixPath(path).stem
                    if not re.fullmatch('[a-z0-9][a-z0-9-]*',name): raise CatalogError('Invalid component identifier')
                    id=('skill:' if kind=='skills' else 'command:')+name
                    if id in seen_skills and seen_skills[id]!=path: raise CatalogError(f'Duplicate skill ID: {name}')
                    seen_skills[id]=path
                    details={'user_invocable':data.get('user-invocable',True),'disable_model_invocation':data.get('disable-model-invocation',False)}
                    if any(not isinstance(v,bool) for v in details.values()): raise CatalogError('Invalid skill visibility')
                    add(Capability(id,'skill' if kind=='skills' else 'command',name,data['description'],[snapshot.source(path)],[client],details))
        for path,inline in paths['hooks']:
            hooks=(inline if inline is not None else json_file(snapshot,path)).get('hooks')
            if not isinstance(hooks,dict): raise CatalogError(f'Invalid hook config: {path}')
            for event,groups in hooks.items():
                if not isinstance(groups,list): raise CatalogError('Invalid hook registration')
                for i,group in enumerate(groups):
                    actions=group.get('hooks')
                    if not isinstance(actions,list): raise CatalogError('Invalid hook action list')
                    for j,action in enumerate(actions):
                        pointer=f'/hooks/{event}/{i}/hooks/{j}'
                        # Never expose shell commands; link to the reviewed definition instead.
                        details={'event':event,'matcher':group.get('matcher','All tools'),'type':action.get('type'),'timeout_seconds':action.get('timeout'),'pointer':pointer}
                        id=f'hook:{event}:{i}:{j}'
                        identity=json.dumps({'action':action,'group':{k:v for k,v in group.items() if k!='hooks'}},sort_keys=True)
                        if id in hook_identities and hook_identities[id]!=identity:
                            raise CatalogError(f'Conflicting hook handlers: {id}')
                        hook_identities[id]=identity
                        add(Capability(id,'hook',event,None,[snapshot.source(path,pointer)],[client],details))
        servers={}
        for path,inline in paths['mcpServers']:
            obj=inline if inline is not None else json_file(snapshot,path)
            values=obj.get('mcpServers',obj if inline else None)
            if not isinstance(values,dict): raise CatalogError('Invalid MCP config')
            for name,value in values.items():
                if not isinstance(value,dict): raise CatalogError('Invalid MCP server')
                transport=value.get('type','stdio' if 'command' in value else 'http')
                if transport=='streamable-http': transport='http'
                endpoint=value.get('url')
                if endpoint:
                    parsed=urlsplit(endpoint)
                    if parsed.scheme!='https' or parsed.username or parsed.password or parsed.query or parsed.fragment:
                        raise CatalogError('MCP endpoint cannot be safely published')
                servers[name]=Capability('mcp_server:'+name,'mcp_server',name,None,[snapshot.source(path)],[client],{'transport':transport,'endpoint':endpoint})
        for name,cap in servers.items():
            key=cap.id
            if key in found and found[key].details!=cap.details:
                cap.id+=':'+client
                diagnostics.append(f'{name}: client configurations differ')
            add(cap)
    if config.tool_source:
        source=config.tool_source; snapshot.source(source)
        text=snapshot.files[source].decode()
        # This adapter only accepts literal tool(name, title, description, ...) declarations.
        pattern=r'\btool\(\s*("(?:[^"\\]|\\.)*")\s*,\s*("(?:[^"\\]|\\.)*")\s*,\s*("(?:[^"\\]|\\.)*")\s*,'
        declarations=re.findall(pattern,text)
        if not declarations or len(declarations)!=len(re.findall(r'\btool\(',text)):
            raise CatalogError('Tool declaration adapter drifted')
        table=BeautifulSoup(snapshot.files['docs/pages/reference.html'],'html.parser')
        documented={row.select_one('td code').get_text() for row in table.select('tr') if row.select_one('td code') and row.select_one('td code').get_text().startswith('trakt_')}
        if {json.loads(d[0]) for d in declarations}!=documented: raise CatalogError('Tool declarations and documentation disagree')
        for raw_name,title,description in declarations:
            name=json.loads(raw_name)
            add(Capability('mcp_tool:'+name,'mcp_tool',name,json.loads(description),[snapshot.source(source)],['claude','codex'],{'server_id':'trakt','title':json.loads(title)}))
    return sorted(found.values(),key=lambda c:(c.kind,c.id)),diagnostics


def capability_counts(items):
    return {'skills':sum(c.kind=='skill' for c in items),'mcp_servers':sum(c.kind=='mcp_server' for c in items),'mcp_tools':sum(c.kind=='mcp_tool' for c in items),'hook_actions':sum(c.kind=='hook' for c in items),'hook_events':len({c.details['event'] for c in items if c.kind=='hook'}),'standalone_commands':sum(c.kind=='command' for c in items)}
