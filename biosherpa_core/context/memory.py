"""Memory interface -- reserved for future implementation.

Currently defines the contract without any storage backend.
Future implementations will support conversation, project, and
analysis memory backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class MemoryProvider(ABC):
    """Abstract interface for persistence of agent state.

    Subclasses implement concrete storage (e.g. file-based, SQLite,
    vector store).  The interface is intentionally minimal so that
    early-stage agents can function without a complex backend.
    """

    @abstractmethod
    def save(self, key: str, value: Dict[str, Any]) -> None:
        """Persist a key-value record."""
        ...

    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a previously saved record, or None."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored records."""
        ...
