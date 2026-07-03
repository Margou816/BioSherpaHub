"""Unit tests for the DESeq2 analysis handler.

Tests validation, command building, and output collection logic.
Does NOT require R to be installed (subprocess is mocked).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_TOOL_DIR = Path(__file__).resolve().parents[1] / "tools" / "deseq2_analysis"
sys.path.insert(0, str(_TOOL_DIR))

from handler import (
    _check_counts_header,
    _check_metadata_header,
    build_command,
    collect_outputs,
    validate_inputs,
)


class TestValidateInputs:
    def test_valid_inputs(self, sample_counts, sample_metadata, sample_output_dir):
        paths = validate_inputs(sample_counts, sample_metadata, sample_output_dir, 0.05, 1.0)
        assert paths["counts"].exists()
        assert paths["metadata"].exists()

    def test_missing_counts_file(self, sample_metadata, sample_output_dir):
        with pytest.raises(FileNotFoundError):
            validate_inputs(Path("/nonexistent/counts.csv"), sample_metadata, sample_output_dir, 0.05, 1.0)

    def test_missing_metadata_file(self, sample_counts, sample_output_dir):
        with pytest.raises(FileNotFoundError):
            validate_inputs(sample_counts, Path("/nonexistent/meta.csv"), sample_output_dir, 0.05, 1.0)

    def test_alpha_out_of_range(self, sample_counts, sample_metadata, sample_output_dir):
        with pytest.raises(ValueError, match="alpha"):
            validate_inputs(sample_counts, sample_metadata, sample_output_dir, 0.0, 1.0)
        with pytest.raises(ValueError, match="alpha"):
            validate_inputs(sample_counts, sample_metadata, sample_output_dir, 1.5, 1.0)

    def test_lfc_threshold_negative(self, sample_counts, sample_metadata, sample_output_dir):
        with pytest.raises(ValueError, match="lfc_threshold"):
            validate_inputs(sample_counts, sample_metadata, sample_output_dir, 0.05, -1.0)

    def test_counts_header_too_short(self, tmp_path):
        path = tmp_path / "bad_counts.csv"
        path.write_text("gene_id\n")
        with pytest.raises(ValueError, match="header"):
            _check_counts_header(path)

    def test_metadata_header_too_short(self, tmp_path):
        path = tmp_path / "bad_meta.csv"
        path.write_text("sample\n")
        with pytest.raises(ValueError, match="header"):
            _check_metadata_header(path)


class TestBuildCommand:
    def test_basic_command(self, sample_counts, sample_metadata, sample_output_dir):
        cmd = build_command(
            counts_file=sample_counts,
            metadata_file=sample_metadata,
            design_formula="~ condition",
            contrast_variable="condition",
            treatment_group="treated",
            control_group="control",
            output_dir=sample_output_dir,
            alpha=0.05,
            lfc_threshold=1.0,
        )
        assert cmd[0] == "Rscript"
        assert str(sample_counts) in cmd
        assert "~ condition" in cmd

    def test_command_includes_all_required_args(self, sample_counts, sample_metadata, sample_output_dir):
        cmd = build_command(
            counts_file=sample_counts,
            metadata_file=sample_metadata,
            design_formula="~ batch + condition",
            contrast_variable="condition",
            treatment_group="mutant",
            control_group="wt",
            output_dir=sample_output_dir,
            alpha=0.01,
            lfc_threshold=2.0,
        )
        assert "--counts" in cmd
        assert "--metadata" in cmd
        assert "--design" in cmd
        assert "--contrast-variable" in cmd
        assert "--treatment" in cmd
        assert "--control" in cmd


class TestCollectOutputs:
    def test_all_outputs_present(self, tmp_path):
        output_dir = tmp_path / "complete_output"
        output_dir.mkdir()
        for fname in ["deseq2_results.csv", "volcano.png", "pca.png", "ma.png", "summary.json"]:
            (output_dir / fname).write_text("placeholder")
        outputs = collect_outputs(output_dir)
        assert "deseq2_results.csv" in outputs

    def test_missing_output_raises(self, tmp_path):
        output_dir = tmp_path / "incomplete_output"
        output_dir.mkdir()
        (output_dir / "deseq2_results.csv").write_text("data")
        with pytest.raises(FileNotFoundError):
            collect_outputs(output_dir)

    def test_summary_json_parsed(self, tmp_path):
        output_dir = tmp_path / "summary_output"
        output_dir.mkdir()
        for fname in ["deseq2_results.csv", "volcano.png", "pca.png", "ma.png"]:
            (output_dir / fname).write_text("placeholder")
        summary = {"upregulated": 50, "downregulated": 30}
        (output_dir / "summary.json").write_text(json.dumps(summary))
        outputs = collect_outputs(output_dir)
        assert outputs["_summary"] == summary


class TestMain:
    def test_main_validation_error(self, tmp_path):
        from handler import main
        result = main([
            "--counts-file", str(tmp_path / "nope.csv"),
            "--metadata-file", str(tmp_path / "meta.csv"),
            "--design-formula", "~ condition",
            "--contrast-variable", "condition",
            "--treatment-group", "treat",
            "--control-group", "ctrl",
            "--output-dir", str(tmp_path / "out"),
        ])
        assert result == 1

    def test_main_success_path(self, tmp_path):
        from handler import main
        counts = tmp_path / "counts.csv"
        counts.write_text("gene_id,s1,s2\nG1,10,20\n")
        meta = tmp_path / "metadata.csv"
        meta.write_text("sample,cond\ns1,A\ns2,B\n")
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        for fname in ["deseq2_results.csv", "volcano.png", "pca.png", "ma.png"]:
            (out_dir / fname).write_text("placeholder")
        (out_dir / "summary.json").write_text('{"total_genes":2}')
        mock_result = MagicMock()
        mock_result.stdout = "Analysis complete"
        mock_result.stderr = ""
        with patch("handler.run_analysis", return_value=mock_result):
            result = main([
                "--counts-file", str(counts),
                "--metadata-file", str(meta),
                "--design-formula", "~ cond",
                "--contrast-variable", "cond",
                "--treatment-group", "A",
                "--control-group", "B",
                "--output-dir", str(out_dir),
            ])
            assert result == 0


# ---------------------------------------------------------------------------
# Fixtures (defined at module level for pytest collection)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_counts(tmp_path: Path) -> Path:
    path = tmp_path / "counts.csv"
    path.write_text("gene_id,sample1,sample2\nGENE1,100,200\nGENE2,300,400\n")
    return path


@pytest.fixture
def sample_metadata(tmp_path: Path) -> Path:
    path = tmp_path / "metadata.csv"
    path.write_text("sample,condition\nsample1,treated\nsample2,control\n")
    return path


@pytest.fixture
def sample_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"
