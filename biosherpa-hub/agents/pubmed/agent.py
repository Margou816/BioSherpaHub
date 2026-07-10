"""PubMed agent -- thin tool dispatcher (pure Python, no R)."""
from __future__ import annotations
import subprocess, sys, os
from pathlib import Path
from typing import Dict, Any

_HERE = Path(__file__).resolve().parent.parent.parent

TOOLS: Dict[str, Path] = {
    "pubmed_search": _HERE / "tools" / "pubmed_search" / "handler.py",
}

_PARAM_MAP: Dict[str, Dict[str, str]] = {
    "pubmed_search": {
        "query": "--query", "max_results": "--max-results", "output_dir": "--output-dir",
    },
}

def execute_tool(tool_name: str, params: Dict[str, Any], r_libs_user: str = "") -> Dict[str, Any]:
    if tool_name not in TOOLS:
        return {"status": "error", "summary": f"Unknown tool: {tool_name}", "errors": [f"Tool '{tool_name}' not in pubmed agent"]}
    handler = TOOLS[tool_name]
    mapping = _PARAM_MAP.get(tool_name, {})
    cmd = [sys.executable, str(handler)]
    for key, flag in mapping.items():
        if key in params and params[key] != "":
            cmd.extend([flag, str(params[key])])
    outdir = params.get("output_dir", "biosherpa_output")
    Path(outdir).mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        stderr_out = stderr  # R warnings may produce non-zero exit on success failed (exit {result.returncode})", "errors": [stderr], "stderr": stderr}
        return {"status": "success", "summary": f"{tool_name} completed", "stderr": stderr}
    except subprocess.TimeoutExpired:
        return {"status": "error", "summary": f"Tool {tool_name} timed out", "errors": ["Timeout after 120s"]}
    except Exception as exc:
        return {"status": "error", "summary": str(exc), "errors": [str(exc)]}