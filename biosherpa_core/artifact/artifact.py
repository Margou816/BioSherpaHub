"""Unified Artifact types for BioSherpa analysis outputs.

Every tool invocation produces one or more Artifacts.
Artifacts carry a stable identity, type discriminator, and metadata
so that downstream consumers (planners, reporters, UIs) can
reason about them uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Optional, Union
from uuid import uuid4


class ArtifactType(Enum):
    """Well-known artifact types."""
    TABLE = auto()       # CSV, TSV, DataFrame
    IMAGE = auto()       # PNG, SVG
    REPORT = auto()      # HTML, PDF, DOCX
    RDS = auto()         # R serialised object
    DIRECTORY = auto()   # Collection of related files
    LOG = auto()         # Execution log
    JSON = auto()        # Structured JSON
    OTHER = auto()


@dataclass
class Artifact:
    """A single output produced by a tool or agent.

    Attributes:
        id:          Stable UUID generated at creation time.
        name:        Human-readable label (e.g. "volcano_plot").
        artifact_type: Discriminator for consumers.
        path:        Filesystem location, or None for in-memory artifacts.
        description: Free-text explanation of what the artifact contains.
        metadata:    Arbitrary key-value pairs for extensibility.
    """
    name: str
    artifact_type: ArtifactType
    path: Optional[Path] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)

    @classmethod
    def table(cls, name: str, path: Path, **kwargs: Any) -> "Artifact":
        """Convenience factory for a table artifact."""
        return cls(name=name, artifact_type=ArtifactType.TABLE, path=path, **kwargs)

    @classmethod
    def image(cls, name: str, path: Path, **kwargs: Any) -> "Artifact":
        """Convenience factory for an image artifact."""
        return cls(name=name, artifact_type=ArtifactType.IMAGE, path=path, **kwargs)

    @classmethod
    def json_artifact(cls, name: str, path: Path, **kwargs: Any) -> "Artifact":
        """Convenience factory for a JSON artifact."""
        return cls(name=name, artifact_type=ArtifactType.JSON, path=path, **kwargs)

    @classmethod
    def report(cls, name: str, path: Path, **kwargs: Any) -> "Artifact":
        """Convenience factory for a report artifact."""
        return cls(name=name, artifact_type=ArtifactType.REPORT, path=path, **kwargs)
