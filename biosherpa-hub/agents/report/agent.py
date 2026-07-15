"""Report agent -- generates combined analysis report."""
from __future__ import annotations
import subprocess, sys, os, json
from pathlib import Path
from typing import Dict, Any

_HERE = Path(__file__).resolve().parent.parent.parent
_HANDLER = _HERE / "tools" / "report" / "handler.py"

def execute_tool(tool_name: str, params: Dict[str, Any], **kw) -> Dict[str, Any]:
    if tool_name != "report":
        return {"status": "error", "summary": f"Unknown tool: {tool_name}"}
    cmd = [sys.executable, str(_HANDLER)]
    for key in ["diffexp_dir", "enrichment_dir", "pubmed_dir", "output_dir"]:
        val = params.get(key, "")
        if val:
            cmd.extend([f"--{key.replace('_','-')}", str(val)])
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        return {"status": "success", "summary": f"report completed (exit {result.returncode})", "stderr": stderr}
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}