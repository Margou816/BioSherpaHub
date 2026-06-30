"""GitHub-backed agent registry implementation."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from .registry import BaseRegistry, RegistryEntry, RegistryIndex
from .manifest import AgentManifest

@dataclass
class GitHubRegistry(BaseRegistry):
    repo_url: str
    index_path: str = "registry/registry.yaml"
    _index: Optional[RegistryIndex] = None
    def load_index(self) -> RegistryIndex:
        if self._index is not None: return self._index
        raw_url = f"{self.repo_url.rstrip('/')}/refs/heads/main/{self.index_path}"
        entries: List[RegistryEntry] = []
        try:
            import urllib.request, yaml
            with urllib.request.urlopen(raw_url, timeout=30) as resp:
                data = yaml.safe_load(resp.read().decode("utf-8"))
            for item in data.get("entries", []):
                entries.append(RegistryEntry(**{k: v for k, v in item.items() if k in RegistryEntry.__dataclass_fields__}))
        except Exception as exc:
            raise RuntimeError(f"Failed to load registry index from {raw_url}: {exc}")
        self._index = RegistryIndex(entries=entries, metadata=data.get("metadata", {}))
        return self._index
    def search(self, keywords: List[str]) -> List[RegistryEntry]:
        return self.load_index().search(keywords)
    def resolve(self, agent_id: str) -> RegistryEntry:
        entry = self.load_index().by_id(agent_id)
        if entry is None: raise KeyError(f"Agent not found: {agent_id}")
        return entry
    def list_all(self) -> List[RegistryEntry]:
        return list(self.load_index().entries)
    def fetch_manifest(self, entry: RegistryEntry) -> AgentManifest:
        raw_url = f"{entry.repository.rstrip('/')}/refs/heads/main/manifest.yaml"
        try:
            import urllib.request, yaml
            with urllib.request.urlopen(raw_url, timeout=30) as resp:
                data = yaml.safe_load(resp.read().decode("utf-8"))
            return AgentManifest.from_dict(data)
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch manifest for {entry.id}: {exc}")
