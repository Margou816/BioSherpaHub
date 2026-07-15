"""Transcriptome agent -- thin tool dispatcher."""
from pathlib import Path
from shared import dispatch_tool

_HERE = Path(__file__).resolve().parent.parent.parent

TOOLS = {"diffexp": _HERE / "tools" / "diffexp" / "handler.py"}

PARAM_MAP = {"diffexp": {
    "method": "--method", "counts": "--counts", "metadata": "--metadata",
    "design": "--design", "contrast-variable": "--contrast-variable",
    "treatment": "--treatment", "control": "--control",
    "output_dir": "--output-dir", "pvalue_cutoff": "--pvalue-cutoff",
    "use_padj": "--use-padj", "lfc_threshold": "--lfc-threshold",
    "colors": "--colors", "pca_label": "--pca-label",
}}

def execute_tool(tool_name, params, r_libs_user=""):
    env = {"R_LIBS_USER": r_libs_user} if r_libs_user else None
    return dispatch_tool("transcriptome", TOOLS, PARAM_MAP, tool_name, params, timeout=600, env_extra=env)