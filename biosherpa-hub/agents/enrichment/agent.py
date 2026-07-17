"""Enrichment agent -- thin tool dispatcher."""
from pathlib import Path
from shared import dispatch_tool

_HERE = Path(__file__).resolve().parent.parent.parent

TOOLS = {
    "go_enrichment": _HERE / "tools" / "go_enrichment" / "handler.py",
    "kegg_enrichment": _HERE / "tools" / "kegg_enrichment" / "handler.py",
}

PARAM_MAP = {
    "go_enrichment": {"deg_file": "--deg-file", "organism": "--organism",
        "pvalue_cutoff": "--pvalue-cutoff", "qvalue_cutoff": "--qvalue-cutoff",
        "output_dir": "--output-dir"},
    "kegg_enrichment": {"deg_file": "--deg-file", "organism": "--organism",
        "pvalue_cutoff": "--pvalue-cutoff", "qvalue_cutoff": "--qvalue-cutoff",
        "output_dir": "--output-dir"},
}

def execute_tool(tool_name, params, r_libs_user=""):
    env = {"R_LIBS_USER": r_libs_user} if r_libs_user else None
    return dispatch_tool("enrichment", TOOLS, PARAM_MAP, tool_name, params, timeout=1200, env_extra=env)