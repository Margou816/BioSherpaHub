#!/usr/bin/env python
"""run_agent.py -- subprocess entry for MCP Server.

Called: python run_agent.py --agent transcriptome --params '{json}'

Zero biosherpa_core dependency. Uses local core_types.py.
"""
from __future__ import annotations
import argparse, json, sys, importlib
import inspect
from pathlib import Path
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from core_types import Request, Project, ResultStatus
def main(argv=None):
    p = argparse.ArgumentParser(description="BioSherpa Agent Runner")
    p.add_argument("--agent", required=True, help="Agent name (e.g. transcriptome)")
    p.add_argument("--params", required=True, help="JSON params dict")
    p.add_argument("--workspace", default=".", help="Workspace dir")
    args = p.parse_args(argv)
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(json.dumps({"status":"error","summary":f"Invalid JSON params: {e}"}))
        return 1
    project = Project(workspace=Path(args.workspace))
    request = Request(query="", project=project, user_parameters=params)
    try:
        mod = importlib.import_module(f"agents.{args.agent}.agent")
        # Dynamically find the first BaseAgent subclass
        cls = None
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if name.endswith("Agent") and name != "BaseAgent":
                cls = obj; break
        if cls is None:
            raise ImportError(f"No *Agent class found in agents.{args.agent}.agent")
        agent = cls()
        plan = agent.plan(request)
        result = agent.execute(request, plan)
        result.summary = agent.summarize(result)
        artifacts = [{"name":a.name,"type":a.artifact_type.name,"path":str(a.path),"description":a.description} for a in result.artifacts]
        status = "success" if result.status.name == "SUCCESS" else result.status.name.lower()
        out = {"status":status,"summary":result.summary,"artifacts":artifacts,"workflow":plan.tool_sequence}
    except Exception as exc:
        out = {"status":"error","summary":str(exc),"artifacts":[],"errors":[str(exc)]}
    print(json.dumps(out, indent=2, default=str))
    return 0 if out["status"] == "success" else 1
if __name__ == "__main__":
    sys.exit(main())
