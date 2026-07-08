"""PubMed tool runner -- NCBI E-utilities search."""
from __future__ import annotations
import subprocess, sys, os
from pathlib import Path
from typing import Dict, List, Optional
from core_types import Artifact, ArtifactType
_HERE = Path(__file__).resolve().parent.parent.parent
_HANDLER = _HERE / "tools" / "pubmed_search" / "handler.py"
def run_pubmed_search(params: Dict, timeout: int = 120) -> List[Artifact]:
    cmd = [sys.executable, str(_HANDLER)]
    for k in ("query","max_results","output_dir"):
        if k in params: cmd.extend([f"--{k.replace('_','-')}", str(params[k])])
    subprocess.run(cmd, capture_output=True, timeout=timeout, check=True)
    outdir = Path(params.get("output_dir", "."))
    artifacts: List[Artifact] = []
    for f in sorted(outdir.iterdir()):
        if not f.is_file(): continue
        if f.suffix == ".csv": at = ArtifactType.TABLE
        else: at = ArtifactType.OTHER
        artifacts.append(Artifact(name=f.name, artifact_type=at, path=f))
    return artifacts
