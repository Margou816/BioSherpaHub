"""Tests for Artifact."""
import sys
sys.path.insert(0, r'F:\BioSherpa\RD\biosherpa-core')
from biosherpa_core import Artifact, ArtifactType
class TestArtifact:
 def test_table(self, tmp_path):
  a = Artifact.table("r", tmp_path / "r.csv")
  assert a.artifact_type == ArtifactType.TABLE
 def test_unique_id(self):
  a1 = Artifact(name="a", artifact_type=ArtifactType.LOG)
  a2 = Artifact(name="b", artifact_type=ArtifactType.LOG)
  assert a1.id != a2.id
 def test_metadata(self):
  a = Artifact(name="x", artifact_type=ArtifactType.JSON, metadata={"n":1})
  assert a.metadata["n"] == 1
