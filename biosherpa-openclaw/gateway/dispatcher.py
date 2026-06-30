"""BioSherpa Dispatcher -- main entry point for OpenClaw."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from biosherpa_core.registry.github_registry import GitHubRegistry
from biosherpa_core.registry.registry import BaseRegistry
from biosherpa_core.loader.cache import AgentCache
from biosherpa_core.lifecycle.manager import LifecycleManager
from .router import Router
from .adapter import GatewayAdapter
@dataclass
class Dispatcher:
 registry: BaseRegistry; cache: AgentCache
 lifecycle: Optional[LifecycleManager] = None
 router: Optional[Router] = None
 adapter: Optional[GatewayAdapter] = None
 def __post_init__(self):
  self.lifecycle = self.lifecycle or LifecycleManager(registry=self.registry, cache=self.cache)
  self.router = self.router or Router(registry=self.registry)
  self.adapter = self.adapter or GatewayAdapter()
 def dispatch(self, user_message: str, workspace_path: Path, file_paths: Optional[List[Path]] = None) -> dict:
  request = self.adapter.to_biosherpa(user_message, workspace_path, file_paths or [])
  entries = self.router.route(request)
  if not entries: return {"status": "not_handled", "message": None, "artifacts": [], "errors": []}
  result = self.lifecycle.execute(request)
  return self.adapter.to_openclaw(result)
 @classmethod
 def from_github(cls, repo_url: str, cache_dir: str = "~/.biosherpa/cache") -> "Dispatcher":
  cache_path = Path(cache_dir).expanduser().resolve()
  registry = GitHubRegistry(repo_url=repo_url)
  cache = AgentCache(cache_root=cache_path)
  return cls(registry=registry, cache=cache)
