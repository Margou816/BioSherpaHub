"""Tests for TranscriptomeAgent with BioSherpa Core."""
import sys
sys.path.insert(0, r'F:\BioSherpa\RD\biosherpa-openclaw')
import pytest
from pathlib import Path
from biosherpa_core import Request, Project, WorkflowPlan, ResultStatus
from biosherpa_core import Result, Artifact, ArtifactType
@pytest.fixture
def agent():
 from agents.transcriptome.agent import TranscriptomeAgent
 return TranscriptomeAgent()
@pytest.fixture
def request_rna(tmp_path):
 c = tmp_path / "counts.csv"; c.write_text("gene_id,s1,s2\nG1,10,20\n")
 m = tmp_path / "metadata.csv"; m.write_text("sample,cond\ns1,A\ns2,B\n")
 o = tmp_path / "output"
 return Request(query="run deseq2 on rna-seq data", project=Project(workspace=tmp_path),
  user_parameters={"counts_file":str(c),"metadata_file":str(m),
  "design_formula":"~cond","contrast_variable":"cond","treatment_group":"A",
  "control_group":"B","output_dir":str(o)})
@pytest.fixture
def request_other():return Request(query="weather",project=Project(workspace=Path("/tmp")))
class TestCanHandle:
 def test_positive(self,agent,request_rna):assert agent.can_handle(request_rna)
 def test_negative(self,agent,request_other):assert not agent.can_handle(request_other)
 def test_keywords(self,agent):
  for kw in ["rna-seq","DESeq2","transcriptome"]:
   r=Request(query=f"run {kw} analysis",project=Project(workspace=Path("/tmp")))
   assert agent.can_handle(r),f"should match: {kw}"
class TestPlan:
 def test_workflow(self,agent,request_rna):
  wf=agent.plan(request_rna);assert len(wf.steps)==1;assert wf.steps[0].tool=="deseq2_analysis"
 def test_defaults(self,agent,request_rna):
  wf=agent.plan(request_rna);p=wf.steps[0].params
  assert p["alpha"]==0.05;assert p["lfc_threshold"]==1.0
class TestSummarize:
 def test_empty(self,agent):
  r=Result(status=ResultStatus.SUCCESS);assert "no artifacts" in agent.summarize(r).lower()
 def test_with_data(self,agent,tmp_path):
  a1=Artifact.table("csv",tmp_path/"r.csv")
  a2=Artifact(name="summary.json",artifact_type=ArtifactType.JSON,path=tmp_path/"s.json",
   description="DESeq2: 3 of 10 genes significant (0 up,3 down), alpha=0.05")
  r=Result.success(artifacts=[a1,a2]);assert "3 of 10" in agent.summarize(r)
