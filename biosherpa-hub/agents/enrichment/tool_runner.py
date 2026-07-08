"""Enrichment tool runners -- wraps GO and KEGG handler.py for Core."""
from __future__ import annotations
import subprocess, sys, os
from pathlib import Path
from typing import Dict, List, Optional
from core_types import Artifact, ArtifactType

_HERE = Path(__file__).resolve().parent.parent.parent
_GO_HANDLER = _HERE / "tools" / "go_enrichment" / "handler.py"
_KEGG_HANDLER = _HERE / "tools" / "kegg_enrichment" / "handler.py"

def _run_handler(handler: Path, params: Dict, r_libs: Optional[str] = None, timeout: int = 600) -> List[Artifact]:
    cmd = [sys.executable, str(handler)]
    for key in ("deg_file", "organism", "pvalue_cutoff", "qvalue_cutoff", "output_dir"):
        if key in params: cmd.extend([f"--{key.replace('_','-')}", str(params[key])])
    env = None
    if r_libs: env = os.environ.copy(); env["R_LIBS_USER"] = r_libs
    subprocess.run(cmd, capture_output=True, timeout=timeout, env=env, check=True)
    outdir = Path(params.get("output_dir", "."))
    artifacts: List[Artifact] = []
    for f in sorted(outdir.iterdir()):
        if not f.is_file(): continue
        if f.suffix == ".csv": at = ArtifactType.TABLE
        elif f.suffix == ".png": at = ArtifactType.IMAGE
        else: at = ArtifactType.OTHER
        artifacts.append(Artifact(name=f.name, artifact_type=at, path=f))
    return artifacts

def run_go_enrichment(params: Dict, **kw) -> List[Artifact]:
    return _run_handler(_GO_HANDLER, params, **kw)

def run_kegg_enrichment(params: Dict, **kw) -> List[Artifact]:
    return _run_handler(_KEGG_HANDLER, params, **kw)
