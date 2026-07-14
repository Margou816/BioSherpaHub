"""Transcriptome agent -- thin tool dispatcher."""
from __future__ import annotations
import subprocess, sys, os, json
from pathlib import Path
from typing import Dict, Any

_HERE = Path(__file__).resolve().parent.parent.parent

TOOLS: Dict[str, Path] = {
    "diffexp": _HERE / "tools" / "diffexp" / "handler.py",
}

_PARAM_MAP: Dict[str, Dict[str, str]] = {
    "diffexp": {
        "method": "--method",
        "counts": "--counts",
        "metadata": "--metadata",
        "design": "--design",
        "contrast-variable": "--contrast-variable",
        "treatment": "--treatment",
        "control": "--control",
        "output_dir": "--output-dir",
        "pvalue_cutoff": "--pvalue-cutoff",
        "use_padj": "--use-padj",
        "lfc_threshold": "--lfc-threshold",
        "colors": "--colors",
        "pca_label": "--pca-label",
    },
}

def execute_tool(tool_name: str, params: Dict[str, Any], r_libs_user: str = "") -> Dict[str, Any]:
    if tool_name not in TOOLS:
        return {"status": "error", "summary": f"Unknown tool: {tool_name}"}
    handler = TOOLS[tool_name]
    mapping = _PARAM_MAP.get(tool_name, {})
    cmd = [sys.executable, str(handler)]
    for key, flag in mapping.items():
        val = params.get(key, "")
        if isinstance(val, bool):
            if val:
                cmd.append(flag)
        elif val != "" and val is not None:
            cmd.extend([flag, str(val)])
    outdir = params.get("output_dir", "biosherpa_output")
    Path(outdir).mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if r_libs_user:
        env["R_LIBS_USER"] = r_libs_user
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600, env=env)
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        return {"status": "success", "summary": f"{tool_name} completed (exit {result.returncode})", "stderr": stderr}
    except subprocess.TimeoutExpired:
        return {"status": "error", "summary": f"Tool {tool_name} timed out", "errors": ["Timeout after 600s"]}
    except Exception as exc:
        return {"status": "error", "summary": str(exc), "errors": [str(exc)]}