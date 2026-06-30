"""Agent Manifest -- describes a BioSherpa agent package."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AgentManifest:
    """Declares an agent's identity, capabilities, and dependencies.

    Each agent repository contains a manifest.yaml that the registry
    reads without executing any agent code.
    """
    name: str
    version: str
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    domain: str = "general"
    entry: str = ""
    minimum_core_version: str = "0.1.0"
    required_tools: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "AgentManifest":
        """Factory from a parsed YAML/JSON dict."""
        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            keywords=data.get("keywords", []),
            domain=data.get("domain", "general"),
            entry=data.get("entry", ""),
            minimum_core_version=data.get("minimum_core_version", "0.1.0"),
            required_tools=data.get("required_tools", []),
            required_skills=data.get("required_skills", []),
            metadata=data.get("metadata", {}),
        )
