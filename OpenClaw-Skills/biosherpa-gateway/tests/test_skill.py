"""Minimal tests for biosherpa-gateway-skill."""
import sys
sys.path.insert(0, r'F:\BioSherpa\RD')
from config import Config
from cache import SkillCache
from response import format_no_match
class TestConfig:
 def test_defaults(self):
  c=Config()
  assert "Margou816" in c.registry_url
  assert c.agent_timeout_seconds == 600
class TestCache:
 def test_store_get(self, tmp_path):
  c=SkillCache(cache_root=tmp_path/"cache",ttl_seconds=99999)
  src=tmp_path/"src";src.mkdir();(src/"f.txt").write_text("ok")
  p=c.store("test","1.0",src)
  assert c.get("test","1.0") is not None
class TestResponse:
 def test_no_match(self):
  r=format_no_match()
  assert r["status"]=="no_match"
  assert "No Matching Agent" in r["summary"]
