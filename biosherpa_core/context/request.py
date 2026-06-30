"""Unified Request -- the single input type consumed by every BioSherpa agent.

A Request carries the user's intent together with the project context.
It does NOT contain raw chat history; that is the responsibility of
the LLM runtime / adapter layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .project import Project


@dataclass
class Request:
    """A single analysis request from the user.

    Attributes:
        id:              Unique request identifier.
        query:           Natural-language description of what the user wants.
        project:         Snapshot of the project context.
        workspace:       Convenience alias for project.workspace.
        files:           User-provided input files (paths relative to workspace).
        user_parameters: Explicit key-value overrides from the user.
        metadata:        Opaque metadata forwarded by the adapter.
        created_at:      Timestamp of request creation.
    """
    query: str
    project: Project
    workspace: Optional[Path] = None
    files: List[Path] = field(default_factory=list)
    user_parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.workspace is None:
            object.__setattr__(self, "workspace", self.project.workspace)
