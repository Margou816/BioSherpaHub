"""Tests for OpenClaw Adapter."""
import sys
sys.path.insert(0, r'F:\BioSherpa\RD\biosherpa-core')
import pytest
from biosherpa_core.adapter.openclaw import OpenClawAdapter,OpenClawRequest
from biosherpa_core.agent.registry import AgentRegistry
from biosherpa_core.agent.base_agent import BaseAgent
from biosherpa_core import WorkflowPlan,Result
from biosherpa_core.exceptions import AdapterError
class _A(BaseAgent):
 name="adpt"
 def can_handle(self,r):return"rna"in r.query
 def plan(self,r):return WorkflowPlan()
 def execute(self,r,p):
  from biosherpa_core import ResultStatus
  return Result(status=ResultStatus.SUCCESS)
 def summarize(self,r):return"ok"
class TestAdapter:
 def test_translation(self,tmp_path):
  reg=AgentRegistry();reg.register(_A());adp=OpenClawAdapter(reg)
  oc=OpenClawRequest(message="rna-seq",workspace_path=tmp_path)
  bs=adp.to_biosherpa(oc);assert bs.query=="rna-seq"
 def test_routing(self,tmp_path):
  reg=AgentRegistry();reg.register(_A());adp=OpenClawAdapter(reg)
  oc=OpenClawRequest(message="rna analysis",workspace_path=tmp_path)
  bs=adp.to_biosherpa(oc);agent=adp.route(bs);assert agent.name=="adpt"
 def test_no_match(self,tmp_path):
  reg=AgentRegistry();adp=OpenClawAdapter(reg)
  oc=OpenClawRequest(message="other",workspace_path=tmp_path)
  bs=adp.to_biosherpa(oc)
  with pytest.raises(AdapterError):adp.route(bs)
