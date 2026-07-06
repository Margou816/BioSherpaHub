"""DESeq2 tool runner -- wraps handler.py for the BioSherpa Core.

Converts a Core Request into a handler.py CLI invocation,
executes it, and returns a list of typed Artifacts.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from core_types import Artifact, ArtifactType, Project

# Path to handler.py relative to this tool_runner
_HANDLER_DIR = Path(__file__).resolve().parent.parent.parent / "tools" / "deseq2_analysis"
_HANDLER = _HANDLER_DIR / "handler.py"

# Expected output files and their Artifact types
_OUTPUT_SPEC = {
    "deseq2_results.csv": ArtifactType.TABLE,
    "volcano.png": ArtifactType.IMAGE,
    "pca.png": ArtifactType.IMAGE,
    "ma.png": ArtifactType.IMAGE,
    "summary.json": ArtifactType.JSON,
}


# ---------------------------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------------------------

def _extract_params(params: Dict) -> tuple:
    """Extract required and optional parameters for handler.py."""
    required = {}
    for key in ("counts_file", "metadata_file", "design_formula",
                "contrast_variable", "treatment_group", "control_group", "output_dir"):
        if key not in params:
            raise ValueError(f"Missing required parameter: {key}")
        required[key] = str(params[key])
    optional = {}
    for key in ("alpha", "lfc_threshold"):
        if key in params:
            optional[key] = params[key]
    return required, optional


# ---------------------------------------------------------------------------
# Command building
# ---------------------------------------------------------------------------

def _build_command(required: dict, optional: dict) -> List[str]:
    """Build the Rscript command line."""
    cmd = [
        "python", str(_HANDLER),
        "--counts-file", required["counts_file"],
        "--metadata-file", required["metadata_file"],
        "--design-formula", required["design_formula"],
        "--contrast-variable", required["contrast_variable"],
        "--treatment-group", required["treatment_group"],
        "--control-group", required["control_group"],
        "--output-dir", required["output_dir"],
    ]
    if "alpha" in optional:
        cmd.extend(["--alpha", str(optional["alpha"])])
    if "lfc_threshold" in optional:
        cmd.extend(["--lfc-threshold", str(optional["lfc_threshold"])])
    return cmd


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_deseq2(
    params: Dict,
    r_libs_user: Optional[str] = None,
    timeout: int = 600,
) -> List[Artifact]:
    """Run DESeq2 analysis and return typed Artifacts.

    Args:
        params:     Parameter dict matching the handler's CLI interface
                    (counts_file, metadata_file, design_formula, ...).
        r_libs_user:Path to R library directory (default: C:/tmp/Rlib).
        timeout:    Maximum execution time in seconds.

    Returns:
        List of Artifact objects representing the analysis outputs.

    Raises:
        subprocess.CalledProcessError: If the R script exits non-zero.
        ValueError: If required parameters are missing.
    """
    required, optional = _extract_params(params)

    # Ensure output directory exists
    output_dir = Path(required["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = _build_command(required, optional)

    # Set up environment
    env = None
    if r_libs_user:
        import os
        env = os.environ.copy()
        env["R_LIBS_USER"] = r_libs_user

    # Execute
    result = subprocess.run(
        cmd,
        capture_output=True,
        timeout=timeout,
        env=env,
        check=True,
    )

    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    if stderr:
        print(stderr, file=sys.stderr)

    # Collect artifacts
    artifacts: List[Artifact] = []
    for fname, atype in _OUTPUT_SPEC.items():
        fpath = output_dir / fname
        if not fpath.is_file():
            continue
        if atype == ArtifactType.JSON:
            desc = _extract_json_summary(fpath)
        elif atype == ArtifactType.IMAGE:
            desc = f"Plot: {fname.replace('.png','').replace('_',' ').title()}"
        else:
            desc = f"DESeq2 {fname}"
        artifacts.append(Artifact(
            name=fname,
            artifact_type=atype,
            path=fpath,
            description=desc,
        ))
    return artifacts


def _extract_json_summary(path: Path) -> str:
    """Extract key info from summary.json for the artifact description."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return (
            f"DESeq2: {data.get('significant',0)} of {data.get('total_genes',0)} genes "
            f"significant ({data.get('upregulated',0)} up, {data.get('downregulated',0)} down), "
            f"alpha={data.get('alpha',0.05)}, lfc_threshold={data.get('lfc_threshold',1.0)}"
        )
    except Exception:
        return f"DESeq2 summary"
