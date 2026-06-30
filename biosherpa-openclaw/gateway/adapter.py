"""GatewayAdapter -- format translator between raw user input and Core types."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from biosherpa_core.context.request import Request
from biosherpa_core.context.result import Result
from biosherpa_core.context.project import Project

class GatewayAdapter:
    """Translates raw OpenClaw user input into BioSherpa Core types."""
    def to_biosherpa(self, message: str, workspace: Path, files: List[Path]) -> Request:
        project = Project(workspace=workspace, uploaded_files=[p.resolve() for p in files])
        return Request(query=message, project=project, files=files)
    def to_openclaw(self, result: Result) -> dict:
        return {
            "status": "handled" if result.errors else "success",
            "message": result.summary or None,
            "artifacts": [str(a.path) for a in result.artifacts if a.path],
            "errors": result.errors,
        }
