"""Codegen agent -- thin dispatcher for master analysis script generation."""
from __future__ import annotations
import subprocess, sys, os, json
from pathlib import Path
from typing import Dict, Any

_HERE = Path(__file__).resolve().parent.parent.parent
_HANDLER = _HERE / "tools" / "codegen" / "handler.py"

def execute_tool(tool_name: str, params: Dict[str, Any], **kw) -> Dict[str, Any]:
    if tool_name != "codegen":
        return {"status": "error", "summary": f"Unknown tool: {tool_name}"}
    cmd = [sys.executable, str(_HANDLER)]
    for key in ["diffexp-dir", "enrichment-dir", "pubmed-dir", "output-dir"]:
        val = params.get(key.replace("-", "_"), "")
        if val:
            cmd.extend([f"--{key}", str(val)])
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
        return {"status": "success", "summary": stdout.strip() or "codegen completed", "stderr": stderr}
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}