"""Custom exceptions for BioSherpa Core.

All exceptions inherit from BioSherpaError so consumers can
catch a single base type when handling BioSherpa-specific errors.
"""

from __future__ import annotations


class BioSherpaError(Exception):
    """Base exception for all BioSherpa errors."""
    pass


class AgentNotFoundError(BioSherpaError):
    """Raised when a requested agent is not registered."""
    pass


class AgentRegistrationError(BioSherpaError):
    """Raised when agent registration fails (e.g. duplicate name)."""
    pass


class ArtifactNotFoundError(BioSherpaError):
    """Raised when a requested artifact does not exist."""
    pass


class WorkflowError(BioSherpaError):
    """Raised when a workflow plan is malformed or cannot be executed."""
    pass


class AdapterError(BioSherpaError):
    """Raised when an adapter cannot translate between formats."""
    pass


class ProjectError(BioSherpaError):
    """Raised when project context is invalid or missing required data."""
    pass
