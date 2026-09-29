"""Validated catalog records and deterministic serialization."""
from dataclasses import asdict, dataclass, field, is_dataclass
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import quote

REPOSITORIES = frozenset(f'swack-tools/{name}-ai-plugin' for name in ('vale', 'trakt', 'token-max'))

class CatalogError(ValueError):
    """A safe, actionable build failure."""


def relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise CatalogError('Invalid relative source path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) == '.':
        raise CatalogError('Source path must stay inside the repository')
    return str(path)


@dataclass
class SourceRef:
    repo: str
    commit: str
    path: str
    locator: str = ''

    def __post_init__(self):
        if self.repo not in REPOSITORIES or not re.fullmatch(r'[0-9a-f]{40}', self.commit):
            raise CatalogError('Source requires an allowlisted repository and full commit SHA')
        self.path = relative_path(self.path)

    @property
    def url(self):
        return f'https://github.com/{self.repo}/blob/{self.commit}/{quote(self.path, safe="/")}'


@dataclass
class ProjectConfig:
    id: str
    name: str
    repo: str
    ref: str
    plugin_root: str
    homepage: str
    accent: str
    documents: dict
    release_assets: dict
    tool_source: str | None = None


@dataclass
class SourceSnapshot:
    project_id: str
    repo: str
    commit: str
    commit_date: str
    files: dict[str, bytes]
    release_candidates: list = field(default_factory=list)

    def source(self, path, locator=''):
        if path not in self.files:
            raise CatalogError(f'{self.project_id}: source file missing: {relative_path(path)}')
        return SourceRef(self.repo, self.commit, path, locator)


@dataclass
class Capability:
    id: str
    kind: str
    name: str
    description: str | None
    sources: list[SourceRef]
    clients: list[str]
    details: dict = field(default_factory=dict)
    examples: list[dict] = field(default_factory=list)


@dataclass
class VerifiedRelease:
    tag: str
    commit: str
    url: str
    published_at: str
    assets: dict
    release_id: int | None = None
    checksum_asset: dict = field(default_factory=dict)


@dataclass
class PluginRecord:
    id: str
    name: str
    summary: str
    source_version: str
    source_commit: str
    homepage: str
    repo: str
    accent: str
    capabilities: list[Capability]
    counts: dict
    overview: list
    examples: list
    usage: list
    changes: list
    release: VerifiedRelease | None
    diagnostics: list = field(default_factory=list)
    pending_releases: list = field(default_factory=list)


def serialize_catalog(value) -> bytes:
    def default(item):
        if is_dataclass(item):
            return asdict(item)
        raise TypeError('Unsupported catalog value')
    return (json.dumps(value, default=default, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()


def load_registry(path: Path) -> list[ProjectConfig]:
    import jsonschema
    value = json.loads(path.read_text())
    schema = json.loads(path.with_suffix('.schema.json').read_text())
    jsonschema.validate(value, schema)
    projects = [ProjectConfig(**p) for p in value['projects']]
    if len({p.id for p in projects}) != len(projects):
        raise CatalogError('Duplicate project ID')
    for p in projects:
        if p.repo not in REPOSITORIES:
            raise CatalogError('Repository is not allowlisted')
        relative_path(p.plugin_root)
        for selector in p.documents.values():
            relative_path(selector['path'])
    return projects
