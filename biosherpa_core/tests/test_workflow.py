"""Tests for WorkflowPlan."""
import sys
sys.path.insert(0, r'F:\BioSherpa\RD\biosherpa-core')
from biosherpa_core import WorkflowPlan
class TestWorkflow:
 def test_sequence(self):
  wf = WorkflowPlan(name="pipe")
  wf.add_step("deseq2")
  wf.add_step("go", depends_on=[0])
  assert wf.tool_sequence == ["deseq2","go"]
 def test_empty(self):
  wf = WorkflowPlan()
  assert wf.tool_sequence == []
 def test_add_step_returns_index(self):
  wf = WorkflowPlan()
  assert wf.add_step("x") == 0
  assert wf.add_step("y") == 1
