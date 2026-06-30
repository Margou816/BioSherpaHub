"""Abstract Registry interface and index types for BioSherpa agent discovery."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .manifest import AgentManifest

@dataclass(frozen=True)
class RegistryEntry:
    id: str; name: str; description: str = ""
    keywords: List[str] = field(default_factory=list)
    repository: str = ""; version: str = "0.0.0"
    entry: str = ""; manifest: Optional[AgentManifest] = None

@dataclass
class RegistryIndex:
    entries: List[RegistryEntry] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    def by_id(self, agent_id: str) -> Optional[RegistryEntry]:
        for e in self.entries:
            if e.id == agent_id: return e
        return None
    def search(self, keywords: List[str]) -> List[RegistryEntry]:
        lower = {k.lower() for k in keywords}
        results: List[RegistryEntry] = []
        for e in self.entries:
            et = " ".join(e.keywords + [e.name, e.description]).lower()
            if any(kw in et for kw in lower): results.append(e)
        return results

class BaseRegistry(ABC):
    @abstractmethod
    def load_index(self) -> RegistryIndex: ...
    @abstractmethod
    def search(self, keywords: List[str]) -> List[RegistryEntry]: ...
    @abstractmethod
    def resolve(self, agent_id: str) -> RegistryEntry: ...
    @abstractmethod
    def list_all(self) -> List[RegistryEntry]: ...
    @abstractmethod
    def fetch_manifest(self, entry: RegistryEntry) -> AgentManifest: ...
