"""Request routing -- matches user requests to agent entries."""
from __future__ import annotations
from typing import List
from biosherpa_core.context.request import Request
from biosherpa_core.registry.registry import BaseRegistry, RegistryEntry
from biosherpa_core.agent.registry import AgentRegistry
from biosherpa_core.agent.base_agent import BaseAgent

class Router:
    """Routes incoming requests to matching agent entries via the registry."""
    def __init__(self, registry: BaseRegistry, local_agents: AgentRegistry = None):
        self.registry = registry
        self.local_agents = local_agents or AgentRegistry()
    def route(self, request: Request) -> List[RegistryEntry]:
        keywords = request.query.split()
        entries = self.registry.search(keywords)
        return entries[:1] if entries else []
    def route_local(self, request: Request) -> List[BaseAgent]:
        return [a for a in self.local_agents if a.can_handle(request)]
