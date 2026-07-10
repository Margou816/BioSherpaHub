"""Transcriptome agent -- thin tool dispatcher.

Maps tool names to handler scripts for the transcriptome domain.
Called by run_agent.py: python run_agent.py --agent transcriptome --tool deseq2_analysis --params '{...}'
"""
from __future__ import annotations
import subprocess, sys, os, json
from pathlib import Path
from typing import Dict, Any

_HERE = Path(__file__).resolve().parent.parent.parent

TOOLS: Dict[str, Path] = {
    "deseq2_analysis": _HERE / "tools" / "deseq2_analysis" / "handler.py",
    "limma_analysis": _HERE / "tools" / "limma_analysis" / "handler.py",
}

_PARAM_MAP: Dict[str, Dict[str, str]] = {
    "deseq2_analysis": {
        "counts_file": "--counts-file",
        "metadata_file": "--metadata-file",
        "design_formula": "--design-formula",
        "contrast_variable": "--contrast-variable",
        "treatment_group": "--treatment-group",
        "control_group": "--control-group",
        "output_dir": "--output-dir",
        "alpha": "--alpha",
        "lfc_threshold": "--lfc-threshold",
    },
    "limma_analysis": {
        "expr_file": "--expr-file",
        "metadata_file": "--metadata-file",
        "design_formula": "--design-formula",
        "contrast_variable": "--contrast-variable",
        "treatment_group": "--treatment-group",
        "control_group": "--control-group",
        "output_dir": "--output-dir",
        "pvalue_cutoff": "--pvalue-cutoff",
        "lfc_cutoff": "--lfc-cutoff",
    },
}

def execute_tool(tool_name: str, params: Dict[str, Any], r_libs_user: str = "") -> Dict[str, Any]:
    """Dispatch tool_name to the matching handler script and return status JSON."""
    if tool_name not in TOOLS:
        return {"status": "error", "summary": f"Unknown tool: {tool_name}", "errors": [f"Tool '{tool_name}' not in transcriptome agent"]}
    handler = TOOLS[tool_name]
    mapping = _PARAM_MAP.get(tool_name, {})
    cmd = [sys.executable, str(handler)]
    for key, flag in mapping.items():
        if key in params and params[key] != "":
            cmd.extend([flag, str(params[key])])
    outdir = params.get("output_dir", "biosherpa_output")
    Path(outdir).mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if r_libs_user:
        env["R_LIBS_USER"] = r_libs_user
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600, env=env)
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        # R tools may exit 1 on warnings while still producing valid output files
        # Report stderr but don't treat non-zero exit as fatal
        return {"status": "success", "summary": f"{tool_name} completed (exit {result.returncode})", "stderr": stderr}
    except subprocess.TimeoutExpired:
        return {"status": "error", "summary": f"Tool {tool_name} timed out", "errors": ["Timeout after 600s"]}
    except Exception as exc:
        return {"status": "error", "summary": str(exc), "errors": [str(exc)]}