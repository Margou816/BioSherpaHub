"""BioSherpa Core Types — self-contained dataclass copies.

Zero biosherpa_core dependency. Used by run_agent.py and all agents
inside biosherpa-hub.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

class ResultStatus(Enum):
    SUCCESS = auto(); PARTIAL = auto(); FAILED = auto(); CANCELLED = auto()

class ArtifactType(Enum):
    TABLE = auto(); IMAGE = auto(); REPORT = auto(); RDS = auto()
    DIRECTORY = auto(); LOG = auto(); JSON = auto(); OTHER = auto()

@dataclass
class Artifact:
    name: str; artifact_type: ArtifactType
    path: Optional[Path] = None; description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)
    @classmethod
    def table(cls, name: str, path: Path, **kw) -> "Artifact":
        return cls(name=name, artifact_type=ArtifactType.TABLE, path=path, **kw)
    @classmethod
    def image(cls, name: str, path: Path, **kw) -> "Artifact":
        return cls(name=name, artifact_type=ArtifactType.IMAGE, path=path, **kw)
    @classmethod
    def json_artifact(cls, name: str, path: Path, **kw) -> "Artifact":
        return cls(name=name, artifact_type=ArtifactType.JSON, path=path, **kw)

@dataclass(frozen=True)
class SampleInfo:
    sample_id: str; group: str
    metadata: Dict[str, str] = field(default_factory=dict)

@dataclass
class Project:
    workspace: Path
    uploaded_files: List[Path] = field(default_factory=list)
    generated_files: List[Path] = field(default_factory=list)
    samples: List[SampleInfo] = field(default_factory=list)

@dataclass
class Request:
    query: str; project: Project
    user_parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)

@dataclass
class WorkflowStep:
    tool: str; params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)
    description: str = ""

@dataclass
class WorkflowPlan:
    steps: List[WorkflowStep] = field(default_factory=list)
    name: str = ""; description: str = ""
    id: str = field(default_factory=lambda: uuid4().hex)
    def add_step(self, tool: str, params: Optional[Dict[str, Any]] = None,
                 depends_on: Optional[List[int]] = None, description: str = "") -> int:
        self.steps.append(WorkflowStep(tool=tool, params=params or {},
            depends_on=depends_on or [], description=description))
        return len(self.steps) - 1
    @property
    def tool_sequence(self) -> List[str]:
        return [s.tool for s in self.steps]

@dataclass
class Result:
    status: ResultStatus; artifacts: List[Artifact] = field(default_factory=list)
    summary: str = ""; errors: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid4().hex)
    @classmethod
    def success(cls, artifacts: List[Artifact], summary: str = "") -> "Result":
        return cls(status=ResultStatus.SUCCESS, artifacts=artifacts, summary=summary)
    @classmethod
    def failure(cls, errors: List[str]) -> "Result":
        return cls(status=ResultStatus.FAILED, errors=errors)
class BaseAgent(ABC):
    """Minimal agent contract for standalone biosherpa-hub agents."""
    name: str = "base"; version: str = "0.0.0"; description: str = ""
    @abstractmethod
    def can_handle(self, request: "Request") -> bool: ...
    @abstractmethod
    def plan(self, request: "Request") -> "WorkflowPlan": ...
    @abstractmethod
    def execute(self, request: "Request", plan: "WorkflowPlan") -> "Result": ...
    @abstractmethod
    def summarize(self, result: "Result") -> str: ...

