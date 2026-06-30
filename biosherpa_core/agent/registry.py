"""Agent Registry -- the canonical index of all known BioSherpa agents.

The registry is deliberately NOT a singleton.  Consumers (adapters,
runtimes, tests) each own their registry instance, making the system
safe to compose and easy to isolate.
"""

from __future__ import annotations

from typing import Dict, Iterator, List, Optional

from ..exceptions import AgentNotFoundError, AgentRegistrationError
from .base_agent import BaseAgent


class AgentRegistry:
    """A collection of registered agents, indexed by name.

    Agents are added via register() and looked up via find().
    Uniqueness is enforced on agent.name.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, agent: BaseAgent) -> None:
        """Register an agent instance.

        Raises AgentRegistrationError if an agent with the same name
        already exists.
        """
        if agent.name in self._agents:
            raise AgentRegistrationError(
                f"Agent '{agent.name}' is already registered."
            )
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> None:
        """Remove an agent by name.  No-op if not found."""
        self._agents.pop(name, None)

    def find(self, name: str) -> BaseAgent:
        """Look up an agent by exact name.

        Raises AgentNotFoundError if not registered.
        """
        agent = self._agents.get(name)
        if agent is None:
            raise AgentNotFoundError(f"Agent '{name}' is not registered.")
        return agent

    def list_agents(self) -> List[str]:
        """Return the names of all registered agents."""
        return list(self._agents.keys())

    def __iter__(self) -> Iterator[BaseAgent]:
        return iter(self._agents.values())

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        return name in self._agents
