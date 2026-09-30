# Maintain the catalog

The static builder reads public plugin repositories at immutable commits. It
parses native metadata, selected documentation, and reviewed examples. It does
not call an AI service, connect to an MCP server, or execute collected code.

## Build locally

Use Python 3.12 and the locked dependencies:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-site.lock
python scripts/build_site.py --offline tests/fixtures/catalog --output build/site
python scripts/check_site.py --site build/site --catalog build/catalog.json
python -m unittest discover -s tests -v
```

For a live build, run:

```sh
python scripts/build_site.py --live --output build/site
```

Public GitHub requests can use `GH_TOKEN` or `GITHUB_TOKEN` from the environment.
Never write tokens into source files. CI uses its read-only built-in token.
Live builds download and verify both client archives for the newest complete
stable release. An incomplete release does not replace an older complete pair.
No complete release means no download buttons for that plugin. Newer incomplete
releases appear as pending while the last complete pair stays available.

To repeat a build from its provenance artifact, use the same marketplace commit
and dependencies, then run:

```sh
python scripts/build_site.py --locked build/sources.lock.json --output build/replay
```

This mode fetches the recorded commits, checks every source digest, and verifies
the recorded releases again. It fails if an asset or tag changed. Release notes
come from the lock. It does not select newer upstream content. Fixture builds
use `--offline` and require no network access.

## Maintain sources and examples

`catalog/projects.json` defines repositories, plugin roots, source selectors,
and expected archive names. Native files define component counts. Claude and
Codex mirrors are deduplicated; tools remain separate from their server.

`catalog-info.json` in an upstream repository can provide overview selectors,
client guidance, structured examples, and hook descriptions. All three plugins
provide this file. Vale supplies separate Claude Code and Codex skill examples,
requirements, host restrictions, and descriptions for each hook action. Trakt
supplies examples and client guidance. Token Max supplies four audit examples.
Native manifests still define capability counts.

The renderer preserves documented client invocations, including namespaced
Codex mentions such as `$vale:check-prose`. Skill-based Claude slash commands
invoke the same skills; standalone command files are counted separately.
The original `prompt` and `source` example fields remain supported through
explicit reviewed mappings.

`catalog/examples.json` fills documentation gaps. Each entry identifies its
capability, input or trigger, prerequisites, expected behavior, and source.
Reviewed examples include source digests. If a referenced file changes, review
the example before updating its digest. Missing or stale examples fail the build.
Do not claim that an illustrative example was executed. Vale's hook descriptions
come from its catalog; concrete hook triggers and outcomes still use reviewed
examples from `catalog/examples.json`. Review changes to `docs/behavior.md`
before refreshing those example digests.

`catalog/prose-edits.json` records small reviewed wording corrections needed for
Vale. Each correction requires the expected source digest. Do not add a global
rewrite that changes commands, technical meaning, or permission requirements.

To add a plugin, extend the repository allowlist, registry, fixtures, examples,
and tests. Unknown manifest shapes and missing declared files are errors.
Parser failures must not become zero capability counts.

## Verify prose

Use Vale 3.23.0 and the reviewed Vale plugin commit pinned in the workflow.
Check out that plugin into an ignored directory, then run:

```sh
python scripts/check_prose.py --plugin-root .cache/vale-plugin/plugins/vale
```

The wrapper checks identical copies because the plugin excludes generated
folders. It uses the bundled policy without suppressions. Authored documentation
and generated pages must have no warnings or errors. Update wording or reviewed
source corrections instead of weakening the rules.

## Refresh and deployment

Pull requests run checks and publish preview artifacts. They cannot deploy.
Pushes to `main`, manual runs on `main`, and the daily schedule build live data.
Only the separate deployment job receives Pages publication permissions.
Failures preserve the previous deployment. The workflow publishes only
`build/site`; source locks and diagnostic reports are separate artifacts.

The site uses the existing `ai.swacktech.com` custom domain. Keep the generated
`CNAME`, canonical links, and sitemap aligned with that domain. Verify the
published site over HTTPS after deployment.

## Update dependencies

Resolve dependency updates with a hash-generating lock tool. For example:

```sh
uv pip compile requirements-site.in --generate-hashes --no-header --output-file requirements-site.lock
```

Install the lock, run the full test suite, build both modes, and check prose.
Pin Actions and the reviewed prose tooling to complete commit hashes.
