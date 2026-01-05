from __future__ import annotations

from dataclasses import dataclass


class McodexError(Exception):
    """Base class for mcodex domain errors."""


class PipelineConfigError(McodexError, ValueError):
    """Raised when pipeline configuration is invalid."""


@dataclass(frozen=True)
class PipelineNotFoundError(McodexError):
    """Raised when a requested pipeline name does not exist."""

    requested: str
    available: tuple[str, ...]

    def __str__(self) -> str:
        if not self.available:
            return f"Pipeline '{self.requested}' not found."

        options = ", ".join(self.available)
        return f"Pipeline '{self.requested}' not found. Available pipelines: {options}."
