"""HTTP client for BioSherpa agent registry."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import urllib.request, yaml
@dataclass
class AgentMeta:
 id: str; name: str; version: str = "0.0.0"
 description: str = ""; keywords: List[str] = field(default_factory=list)
 repository: str = ""; entry: str = ""
@dataclass
class RegistryClient:
 index_url: str
 _cache: Optional[List[AgentMeta]] = None
 def fetch(self) -> List[AgentMeta]:
  if self._cache is not None: return self._cache
  try:
   with urllib.request.urlopen(self.index_url, timeout=30) as r:
    d = yaml.safe_load(r.read().decode("utf-8"))
  except Exception as e: raise RuntimeError(f"Registry fetch failed: {e}")
  self._cache = [AgentMeta(id=i.get("id",""),name=i.get("name",""),version=i.get("version","0.0.0"),
   description=i.get("description",""),keywords=i.get("keywords",[]),
   repository=i.get("repository",""),entry=i.get("entry","")) for i in d.get("entries",[])]
  return self._cache
 def search(self, keywords: List[str]) -> List[AgentMeta]:
  lo = {k.lower() for k in keywords}
  return [a for a in self.fetch() if any(kw in (a.name+" "+" ".join(a.keywords)).lower() for kw in lo)]
