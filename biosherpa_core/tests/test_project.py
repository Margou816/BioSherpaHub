"""Tests for Project context types."""

import sys
sys.path.insert(0, r'F:\BioSherpa\RD\biosherpa-core')
import pytest
from pathlib import Path
from biosherpa_core import Project, SampleInfo
from biosherpa_core.exceptions import ProjectError


class TestProject:
    def test_resolve(self, tmp_path):
        p = Project(workspace=tmp_path)
        assert p.resolve("sub").parent == tmp_path

    def test_validate_ok(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("a")
        p = Project(workspace=tmp_path, uploaded_files=[f])
        assert p.validate_file(f) == f.resolve()

    def test_validate_unknown(self, tmp_path):
        p = Project(workspace=tmp_path)
        with pytest.raises(ProjectError):
            p.validate_file(tmp_path / "x.txt")


class TestSampleInfo:
    def test_creation(self):
        si = SampleInfo(sample_id="s1", group="treated")
        assert si.sample_id == "s1"
