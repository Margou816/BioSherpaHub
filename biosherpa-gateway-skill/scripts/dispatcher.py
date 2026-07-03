"""Dispatcher — orchestrates registry, loader, execution."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from biosherpa_core.context.request import Request
from biosherpa_core.context.project import Project
from config import Config
from cache import SkillCache
from registry_client import RegistryClient
from loader import SkillLoader
from response import format_response, format_no_match
import gc
@dataclass
class Dispatch:
 config: Config; cache: SkillCache; registry: RegistryClient; loader: SkillLoader
 def run(self, query: str, workspace: Path, files: Optional[List[Path]] = None) -> Dict[str, Any]:
  kw = query.split()
  matches = self.registry.search(kw)
  if not matches: return format_no_match()
  meta = matches[0]
  try:
   agent = self.loader.load(meta)
   project = Project(workspace=workspace, uploaded_files=[p.resolve() for p in (files or [])])
   req = Request(query=query, project=project, metadata={"r_libs_user": self.config.r_libs_user})
   plan = agent.plan(req)
   result = agent.execute(req, plan)
   result.summary = agent.summarize(result)
   result.workflow = plan
   del agent; gc.collect()
   return format_response(result)
  except Exception as exc:
   return {"status":"error","summary":str(exc),"artifacts":[],"errors":[str(exc)]}
