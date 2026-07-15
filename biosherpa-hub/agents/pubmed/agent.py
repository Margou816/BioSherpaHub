"""PubMed agent -- thin tool dispatcher."""
from pathlib import Path
from shared import dispatch_tool

_HERE = Path(__file__).resolve().parent.parent.parent

TOOLS = {"pubmed_search": _HERE / "tools" / "pubmed_search" / "handler.py"}

PARAM_MAP = {"pubmed_search": {
    "query": "--query", "max_results": "--max-results", "output_dir": "--output-dir",
}}

def execute_tool(tool_name, params, r_libs_user=""):
    env = {"R_LIBS_USER": r_libs_user} if r_libs_user else None
    return dispatch_tool("pubmed", TOOLS, PARAM_MAP, tool_name, params, timeout=120, env_extra=env)