"""Tests for AgentRegistry."""
import sys
sys.path.insert(0, r'F:\BioSherpa\RD\biosherpa-core')
import pytest
from biosherpa_core.agent.registry import AgentRegistry
from biosherpa_core.agent.base_agent import BaseAgent
from biosherpa_core import WorkflowPlan, Result
from biosherpa_core.exceptions import AgentNotFoundError, AgentRegistrationError
class _Fake(BaseAgent):
 name="fake"
 def can_handle(self,r):return True
 def plan(self,r):return WorkflowPlan()
 def execute(self,r,p):
  from biosherpa_core import ResultStatus
  return Result(status=ResultStatus.SUCCESS)
 def summarize(self,r):return"ok"
class TestRegistry:
 def test_register_find(self):
  reg=AgentRegistry();a=_Fake();reg.register(a);assert reg.find("fake")is a
 def test_duplicate(self):
  reg=AgentRegistry();reg.register(_Fake())
  with pytest.raises(AgentRegistrationError):reg.register(_Fake())
 def test_missing(self):
  reg=AgentRegistry()
  with pytest.raises(AgentNotFoundError):reg.find("nope")
 def test_unregister(self):
  reg=AgentRegistry();reg.register(_Fake());reg.unregister("fake");assert not reg.list_agents()
