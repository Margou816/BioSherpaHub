"""BioSherpa Core -- framework-agnostic agent foundation.

BioSherpa Core provides the abstract contracts (BaseAgent, Request,
Result, Artifact, etc.) that all domain agents implement.  It does
NOT depend on any specific LLM runtime, platform, or framework.
"""

from .agent.base_agent import BaseAgent
from .agent.registry import AgentRegistry
from .context.request import Request
from .context.result import Result, ResultStatus
from .context.project import Project, SampleInfo
from .context.memory import MemoryProvider
from .artifact.artifact import Artifact, ArtifactType
from .planner.workflow import WorkflowPlan, WorkflowStep, StepStatus

__version__ = "0.1.0"

__all__ = [
    "BaseAgent",
    "AgentRegistry",
    "Request",
    "Result",
    "ResultStatus",
    "Project",
    "SampleInfo",
    "MemoryProvider",
    "Artifact",
    "ArtifactType",
    "WorkflowPlan",
    "WorkflowStep",
    "StepStatus",
]
