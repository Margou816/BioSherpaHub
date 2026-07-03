"""Configuration — single source of tunable defaults."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
@dataclass
class Config:
 registry_url: str = "https://raw.githubusercontent.com/Margou816/BioSherpa/main/registry/registry.yaml"
 cache_dir: str = "~/.biosherpa/cache"
 r_libs_user: str = "C:/tmp/Rlib"
 agent_timeout_seconds: int = 600
 cache_ttl_seconds: int = 86400
 @property
 def cache_path(self) -> Path:
  return Path(self.cache_dir).expanduser().resolve()
