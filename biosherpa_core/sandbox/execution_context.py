"""Execution context sandbox for agent isolation."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from biosherpa_core.context.project import Project
from biosherpa_core.context.memory import MemoryProvider

@dataclass
class ExecutionContext:
    """Isolated sandbox within which an agent executes."""
    workspace: Path
    project: Project
    temp_dir: Path
    memory: Optional[MemoryProvider] = None
    logger: Any = None
    cleanup_on_exit: bool = True
    def __post_init__(self):
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    def log(self, message: str):
        if self.logger is not None:
            try: self.logger.info(message)
            except AttributeError: print(f"[ExecutionContext] {message}")
