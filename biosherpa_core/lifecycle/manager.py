"""BioSherpa lifecycle manager."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from biosherpa_core.context.request import Request
from biosherpa_core.context.result import Result, ResultStatus
from biosherpa_core.agent.base_agent import BaseAgent
from biosherpa_core.registry.registry import BaseRegistry, RegistryEntry
from biosherpa_core.loader.cache import AgentCache
from biosherpa_core.sandbox.execution_context import ExecutionContext
from biosherpa_core.context.project import Project

@dataclass
class LifecycleManager:
    """Orchestrates the full agent lifecycle: locate, load, execute, release."""
    registry: BaseRegistry
    cache: AgentCache
    default_timeout: int = 600
    _active_agents: Dict[str, BaseAgent] = field(default_factory=dict)
    def execute(self, request: Request) -> Result:
        entries = self.registry.search(request.query.split())
        if not entries:
            return Result(status=ResultStatus.FAILED, errors=[f"No agent found for: {request.query[:100]}"])
        entry = entries[0]
        try: manifest = self.registry.fetch_manifest(entry)
        except Exception as exc:
            return Result(status=ResultStatus.FAILED, errors=[f"Failed to fetch manifest for {entry.id}: {exc}"])
        try:
            cached = self.cache.get(entry.id, entry.version)
            if cached is None:
                temp_dir = Path(self.cache.cache_root) / f"download_{entry.id}"
                temp_dir.mkdir(parents=True, exist_ok=True)
                import urllib.request, zipfile, io
                zip_url = f"{entry.repository.rstrip('/')}/archive/refs/heads/main.zip"
                with urllib.request.urlopen(zip_url, timeout=60) as resp:
                    with zipfile.ZipFile(io.BytesIO(resp.read())) as zf:
                        zf.extractall(temp_dir)
                cached = self.cache.store(entry.id, entry.version, temp_dir)
            agent = self._load_agent(entry, cached)
            exec_ctx = ExecutionContext(
                workspace=request.workspace or request.project.workspace,
                project=request.project,
                temp_dir=Path(self.cache.cache_root) / f"exec_{entry.id}",
            )
            plan = agent.plan(request)
            result = agent.execute(request, plan)
            result.summary = agent.summarize(result)
            result.workflow = plan
            self.release(entry.id)
            return result
        except Exception as exc:
            return Result(status=ResultStatus.FAILED, errors=[f"Execution failed: {exc}"])
    def _load_agent(self, entry: RegistryEntry, pkg_path: Path) -> BaseAgent:
        import sys, importlib
        agent_dir = pkg_path
        for root, dirs, files in os_walk(agent_dir):
            if "manifest.yaml" in files: agent_dir = Path(root); break
        if str(agent_dir) not in sys.path: sys.path.insert(0, str(agent_dir))
        module_path, class_name = entry.entry.split(":")
        module = importlib.import_module(module_path)
        agent_cls = getattr(module, class_name)
        agent = agent_cls()
        self._active_agents[entry.id] = agent
        return agent
    def release(self, agent_id: str):
        agent = self._active_agents.pop(agent_id, None)
        if agent is None: return
        import gc; gc.collect()

def os_walk(path: Path):
    import os
    for root, dirs, files in os.walk(str(path)):
        yield Path(root), dirs, files
