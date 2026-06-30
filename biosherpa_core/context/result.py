"""Unified Result -- the single output type returned by every BioSherpa agent.

A Result summarises what happened during an agent execution:
whether it succeeded, what workflow was planned, what artifacts were
produced, and any errors or logs generated along the way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..artifact.artifact import Artifact
from ..planner.workflow import WorkflowPlan


class ResultStatus(Enum):
    """Terminal status of an agent execution."""
    SUCCESS = auto()
    PARTIAL = auto()    # Some tools succeeded, some failed
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class Result:
    """Complete output of an agent execution.

    Attributes:
        status:     Terminal status.
        request_id: Correlates this result with the originating Request.
        workflow:   The planned workflow (may be empty if the agent
                    could not produce a plan).
        artifacts:  All artifacts generated during execution.
        logs:       Timestamped log messages.
        summary:    Human-readable summary written by the agent.
        errors:     Non-fatal errors encountered during execution.
        metadata:   Opaque metadata for the adapter layer.
    """
    status: ResultStatus
    artifacts: List[Artifact] = field(default_factory=list)
    workflow: Optional[WorkflowPlan] = None
    logs: List[str] = field(default_factory=list)
    summary: str = ""
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)
    request_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def success(
        cls,
        artifacts: List[Artifact],
        summary: str = "",
        **kwargs: Any,
    ) -> "Result":
        """Factory for a successful result."""
        return cls(
            status=ResultStatus.SUCCESS,
            artifacts=artifacts,
            summary=summary,
            **kwargs,
        )

    @classmethod
    def failure(cls, errors: List[str], **kwargs: Any) -> "Result":
        """Factory for a failed result."""
        return cls(
            status=ResultStatus.FAILED,
            errors=errors,
            **kwargs,
        )
