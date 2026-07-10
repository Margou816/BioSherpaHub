"""BioSherpa Core Types -- minimal shared types for run_agent.py and agents."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

class ArtifactType(Enum):
    TABLE = auto(); IMAGE = auto(); REPORT = auto(); RDS = auto()
    DIRECTORY = auto(); LOG = auto(); JSON = auto(); OTHER = auto()

@dataclass
class Artifact:
    name: str; artifact_type: ArtifactType
    path: Optional[Path] = None; description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)

@dataclass
class Project:
    workspace: Path
    uploaded_files: List[Path] = field(default_factory=list)
    generated_files: List[Path] = field(default_factory=list)