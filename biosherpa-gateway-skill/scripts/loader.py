"""Agent loader — downloads and instantiates agents."""
from __future__ import annotations
from pathlib import Path
import importlib, io, sys, zipfile, urllib.request, os
from cache import SkillCache
from registry_client import AgentMeta
class SkillLoader:
 def __init__(self, cache: SkillCache, timeout: int = 120):
  self.cache = cache; self.timeout = timeout
 def load(self, meta: AgentMeta):
  pkg = self.cache.get(meta.id, meta.version)
  if pkg is None:
   tmp = Path(self.cache.cache_root) / f"dl_{meta.id}"
   tmp.mkdir(parents=True, exist_ok=True)
   zurl = f"{meta.repository.rstrip('/')}/archive/refs/heads/main.zip"
   with urllib.request.urlopen(zurl, timeout=self.timeout) as r:
    with zipfile.ZipFile(io.BytesIO(r.read())) as zf: zf.extractall(tmp)
   pkg = self.cache.store(meta.id, meta.version, tmp)
  root = pkg
  for rp, _, fs in os.walk(str(pkg)):
   if "manifest.yaml" in fs: root = Path(rp); break
  if str(root) not in sys.path: sys.path.insert(0, str(root))
  mod, cls = meta.entry.split(":")
  return getattr(importlib.import_module(mod), cls)()
