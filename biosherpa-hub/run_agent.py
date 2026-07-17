#!/usr/bin/env python
"""run_agent.py -- subprocess entry for MCP Server.

Called: python run_agent.py --agent transcriptome --tool deseq2_analysis --params '{json}'

Loads the agent module, dispatches to execute_tool(), returns JSON to stdout.
"""
from __future__ import annotations
import argparse, json, sys, importlib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

# Verify shared.py exists (required by agents and handlers)
if not (_HERE / "shared.py").is_file():
    print(json.dumps({
        "status": "error",
        "summary": "shared.py not found in agent package. Update BioSherpaHub GitHub repo and clear cache (~/.biosherpa/cache/)."
    }))
    sys.exit(1)

def main(argv=None):
    p = argparse.ArgumentParser(description="BioSherpa Agent Tool Runner")
    p.add_argument("--agent", required=True, help="Agent name (e.g. transcriptome)")
    p.add_argument("--tool", required=True, help="Tool name (e.g. deseq2_analysis)")
    p.add_argument("--params", required=True, help="JSON params dict")
    p.add_argument("--r-libs-user", default="", help="R library path")
    args = p.parse_args(argv)

    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "summary": f"Invalid JSON params: {e}"}))
        return 1

    try:
        mod = importlib.import_module(f"agents.{args.agent}.agent")
        result = mod.execute_tool(args.tool, params, r_libs_user=args.r_libs_user)
    except Exception as exc:
        result = {"status": "error", "summary": str(exc), "errors": [str(exc)]}

    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") == "success" else 1

if __name__ == "__main__":
    sys.exit(main())