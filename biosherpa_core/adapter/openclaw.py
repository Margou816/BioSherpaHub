"""OpenClaw Adapter -- translates between OpenClaw and BioSherpa Core.

This adapter is intentionally THIN.  It contains no business logic,
no analysis decisions, and no knowledge of specific agents or tools.
Its sole job is format translation:

    OpenClaw Request  ->  BioSherpa Request
    BioSherpa Result  ->  OpenClaw Response
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agent.base_agent import BaseAgent
from ..agent.registry import AgentRegistry
from ..context.project import Project, SampleInfo
from ..context.request import Request
from ..context.result import Result
from ..exceptions import AdapterError


# ---------------------------------------------------------------------------
# Types representing the OpenClaw side (minimal surface)
# ---------------------------------------------------------------------------

@dataclass
class OpenClawRequest:
    """Minimal representation of what an OpenClaw session provides.

    In production this would be populated from the actual OpenClaw
    runtime context.  For now it captures the essential fields.
    """
    message: str
    workspace_path: Path
    file_paths: List[Path] = field(default_factory=list)
    user_variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OpenClawResponse:
    """What the adapter returns to OpenClaw."""
    text: str
    artifacts: List[str] = field(default_factory=list)
    status: str = "success"
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class OpenClawAdapter:
    """Thin translation layer between OpenClaw and BioSherpa Core.

    Usage::

        adapter = OpenClawAdapter(registry)
        bs_request = adapter.to_biosherpa(oc_request)
        agent = adapter.route(bs_request)
        bs_result = agent.execute(bs_request, plan)
        oc_response = adapter.to_openclaw(bs_result)
    """

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    # ------------------------------------------------------------------
    # Format translation
    # ------------------------------------------------------------------

    def to_biosherpa(self, oc: OpenClawRequest) -> Request:
        """Convert an OpenClaw request into a BioSherpa Request."""
        project = Project(
            workspace=oc.workspace_path,
            uploaded_files=[Path(p).resolve() for p in oc.file_paths],
        )
        return Request(
            query=oc.message,
            project=project,
            files=[Path(p) for p in oc.file_paths],
            user_parameters=oc.user_variables,
            metadata=oc.metadata,
        )

    def to_openclaw(self, result: Result) -> OpenClawResponse:
        """Convert a BioSherpa Result into an OpenClaw response."""
        return OpenClawResponse(
            text=result.summary,
            artifacts=[str(a.path) for a in result.artifacts if a.path],
            status=result.status.name.lower(),
            errors=result.errors,
        )

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def route(self, request: Request) -> BaseAgent:
        """Find the first registered agent that can handle the request.

        Raises AdapterError if no agent matches.
        """
        for agent in self._registry:
            if agent.can_handle(request):
                return agent
        raise AdapterError(
            "No registered agent can handle request: "
            f"'{request.query[:120]}...'"
        )
