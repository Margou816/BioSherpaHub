"""BaseAgent -- the abstract contract every BioSherpa agent must fulfil.

Agents are the primary extensibility point of BioSherpa Core.
Every domain-specific agent (transcriptome, enrichment, single-cell,
etc.) inherits from BaseAgent and implements the four lifecycle
methods: can_handle, plan, execute, summarize.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..context.request import Request
from ..context.result import Result
from ..planner.workflow import WorkflowPlan


class BaseAgent(ABC):
    """Abstract base class for all BioSherpa agents.

    Subclasses MUST implement all four abstract methods.  The agent
    lifecycle is:

        1. can_handle(request) -> bool
        2. plan(request)       -> WorkflowPlan
        3. execute(plan)       -> List[Artifact]
        4. summarize(result)   -> str

    Agents are stateless by design.  Any persistent state lives in
    the Project or Memory contexts passed via the Request.
    """

    # ------------------------------------------------------------------
    # Metadata (override in subclasses)
    # ------------------------------------------------------------------
    name: str = "base"
    version: str = "0.0.0"
    description: str = ""

    # ------------------------------------------------------------------
    # Lifecycle methods
    # ------------------------------------------------------------------

    @abstractmethod
    def can_handle(self, request: Request) -> bool:
        """Return True if this agent can process the given request.

        The registry calls this on every registered agent to find
        the best match.  Implementations should inspect request.query,
        request.files, or request.user_parameters to make the decision.
        """
        ...

    @abstractmethod
    def plan(self, request: Request) -> WorkflowPlan:
        """Produce a declarative workflow plan for the request.

        This method MUST NOT execute any tools.  It only describes
        what should be done and in what order.
        """
        ...

    @abstractmethod
    def execute(self, request: Request, plan: WorkflowPlan) -> Result:
        """Execute the planned workflow and return a Result.

        The agent is responsible for invoking tools, handling errors,
        and collecting artifacts.  Implementations may delegate tool
        execution to a shared ToolRunner or call tools directly.
        """
        ...

    @abstractmethod
    def summarize(self, result: Result) -> str:
        """Produce a human-readable summary of the analysis result.

        This is typically the text the user sees after execution.
        """
        ...
