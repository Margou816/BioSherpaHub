"""Project context -- the canonical source of truth for file access.

Agents MUST NOT scan the filesystem directly.  All file knowledge
comes from the Project context, which acts as a controlled sandbox.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ..exceptions import ProjectError


@dataclass(frozen=True)
class SampleInfo:
    """Minimal structured metadata about a single biological sample."""
    sample_id: str
    group: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Project:
    """Immutable snapshot of the project context for an Agent request.

    Agents receive a Project and work within it; they never reach
    outside for files.

    Attributes:
        workspace:      Root directory of the project.
        uploaded_files: Files the user explicitly provided (absolute paths).
        generated_files:Files produced by previous tool invocations.
        temp_dir:       Scratch space for intermediate artifacts.
        samples:        Known sample metadata.
    """
    workspace: Path
    uploaded_files: List[Path] = field(default_factory=list)
    generated_files: List[Path] = field(default_factory=list)
    temp_dir: Optional[Path] = None
    samples: List[SampleInfo] = field(default_factory=list)

    def resolve(self, relative: str | Path) -> Path:
        """Resolve a path relative to the workspace."""
        return (self.workspace / relative).resolve()

    def validate_file(self, path: Path) -> Path:
        """Ensure *path* is known to the project and exists.

        Returns the absolute path if valid, otherwise raises ProjectError.
        """
        resolved = path.resolve()
        known = (
            self.uploaded_files
            + self.generated_files
            + ([self.temp_dir] if self.temp_dir else [])
        )
        if not any(resolved == p.resolve() or resolved.is_relative_to(p.resolve()) for p in known):
            raise ProjectError(f"File {resolved} is not known to the project context.")
        if not resolved.exists():
            raise ProjectError(f"File {resolved} does not exist.")
        return resolved
