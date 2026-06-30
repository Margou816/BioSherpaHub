"""WorkflowPlan -- a declarative description of tool invocation order.

A WorkflowPlan is a directed acyclic graph of tool steps.  It describes
WHAT should be executed without performing any execution itself.
Execution is the responsibility of the agent's run loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import uuid4


class StepStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class WorkflowStep:
    """A single step in a workflow plan.

    Attributes:
        tool:       Name of the tool to invoke (e.g. "deseq2_analysis").
        params:     Parameters to pass to the tool.
        depends_on: Indices of steps that must complete before this one.
        description: Human-readable explanation of what this step does.
    """
    tool: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)
    description: str = ""


@dataclass
class WorkflowPlan:
    """Ordered sequence of WorkflowSteps forming an analysis pipeline.

    Attributes:
        steps:      Ordered list of steps.
        name:       Human-readable label for the workflow.
        description: What the workflow accomplishes.
    """
    steps: List[WorkflowStep] = field(default_factory=list)
    name: str = ""
    description: str = ""
    id: str = field(default_factory=lambda: uuid4().hex)

    @property
    def tool_sequence(self) -> List[str]:
        """Return the ordered list of tool names (for display)."""
        return [s.tool for s in self.steps]

    def add_step(
        self,
        tool: str,
        params: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[int]] = None,
        description: str = "",
    ) -> int:
        """Append a step and return its index."""
        self.steps.append(
            WorkflowStep(
                tool=tool,
                params=params or {},
                depends_on=depends_on or [],
                description=description,
            )
        )
        return len(self.steps) - 1
