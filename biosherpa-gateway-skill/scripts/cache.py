"""Local cache for downloaded agent packages."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import json, shutil, time
@dataclass
class SkillCache:
 cache_root: Path; ttl_seconds: int = 86400
 def __post_init__(self):
  self.cache_root.mkdir(parents=True, exist_ok=True)
  self._mp = self.cache_root / "cache_meta.json"
  self._meta: Dict[str, dict] = json.loads(self._mp.read_text(encoding="utf-8")) if self._mp.exists() else {}
 def _save(self):
  self._mp.write_text(json.dumps(self._meta, indent=2), encoding="utf-8")
 def _key(self, aid: str, ver: str) -> str: return f"{aid}@{ver}"
 def get(self, aid: str, ver: str) -> Optional[Path]:
  e = self._meta.get(self._key(aid, ver))
  if e is None: return None
  p = Path(e["path"])
  return p if p.exists() and time.time() - e["cached_at"] < self.ttl_seconds else None
 def store(self, aid: str, ver: str, src: Path) -> Path:
  dest = self.cache_root / self._key(aid, ver)
  if dest.exists(): shutil.rmtree(dest)
  shutil.copytree(src, dest)
  self._meta[self._key(aid, ver)] = {"path": str(dest), "cached_at": time.time(), "version": ver}
  self._save(); return dest
