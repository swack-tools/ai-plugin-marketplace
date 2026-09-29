"""Build the static marketplace from immutable source inputs."""
import argparse
from pathlib import Path


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--live', action='store_true')
    modes.add_argument('--offline', type=Path)
    modes.add_argument('--locked', type=Path, help='Replay pinned sources and reverify locked release assets')
    parser.add_argument('--registry', type=Path, default=Path('catalog/projects.json'))
    parser.add_argument('--output', type=Path, default=Path('build/site'))
    return parser.parse_args()


def main():
    import json
    import subprocess
    from catalog.models import load_registry, serialize_catalog, VerifiedRelease, CatalogError
    from catalog.fetch import GitHubClient, collect_snapshot, load_snapshot, write_source_lock, load_locked_snapshot
    from catalog.inventory import inventory_plugin
    from catalog.documents import enrich_plugin
    from catalog.render import render_site
    from check_site import check_site
    args=arguments()
    try:
        configs=load_registry(args.registry);snapshots=[];releases={};records=[]
        client=GitHubClient() if args.live or args.locked else None
        locked={s["id"]:s for s in json.loads(args.locked.read_text())["sources"]} if args.locked else {}
        for config in configs:
            if args.live or args.locked:
                from catalog.releases import select_release
                snapshot=load_locked_snapshot(config,locked[config.id],client) if args.locked else collect_snapshot(config,Path('.cache/catalog'),client)
                release=select_release(config,snapshot.release_candidates,client)
                if args.locked and serialize_catalog(release)!=serialize_catalog(locked[config.id]['release']):
                    raise CatalogError('Locked release changed')
            else:
                snapshot,raw=load_snapshot(config,args.offline)
                release=VerifiedRelease(**raw) if raw else None
            caps,diagnostics=inventory_plugin(config,snapshot)
            record=enrich_plugin(config,snapshot,caps,release)
            from catalog.releases import pending_releases
            record.pending_releases=pending_releases(snapshot.release_candidates,config.release_assets)
            record.diagnostics.extend(diagnostics)
            records.append(record);snapshots.append(snapshot);releases[config.id]=release
        commit=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
        catalog={'schema_version':1,'marketplace_commit':commit,'projects':records}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        write_source_lock(snapshots,releases,args.output.parent/'sources.lock.json')
        (args.output.parent/'catalog.json').write_bytes(serialize_catalog(catalog))
        render_site(catalog,Path('site/templates'),Path('site/assets'),Path('content'),args.output)
        errors=check_site(args.output,json.loads(serialize_catalog(catalog)))
        (args.output.parent/'catalog-report.json').write_bytes(serialize_catalog({'errors':errors,'mode':'live' if args.live else 'locked' if args.locked else 'offline','projects':[{'id':r.id,'diagnostics':r.diagnostics} for r in records]}))
        if errors: raise CatalogError('; '.join(errors))
        print(f'Built {len(records)} plugins with {sum(len(r.examples) for r in records)} examples.')
        return 0
    except CatalogError as error:
        print('Catalog build failed: '+str(error))
        return 1
    except Exception as error:
        # Exception text can contain a machine path or authenticated URL.
        print('Catalog build failed: '+type(error).__name__+'. Check the selected input files.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
