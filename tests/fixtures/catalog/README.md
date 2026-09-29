# Source fixtures

These selected files come from the public repositories identified by each
`snapshot.json`. They cover native manifests, documentation selectors, and
examples. All three snapshots include the upstream `catalog-info.json` and
the files its selectors reference. They contain no credentials and do not execute upstream code.

Vale uses the MIT license. Trakt uses GPL-3.0-only. Their fixtures
include upstream licenses. Token Max has no license file in the inspected source. Source commits and release metadata are frozen
for offline tests; live builds verify downloads again.

`expected.json` is a reduced rendering fixture. Parser tests use the source
files directly. Update reviewed example digests when intentionally updating
these fixtures.
