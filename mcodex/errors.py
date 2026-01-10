from __future__ import annotations

from dataclasses import dataclass


class McodexError(Exception):
    """Base class for all mcodex domain errors."""


# === Validation Errors ===
class ValidationError(McodexError, ValueError):
    """Base for input validation failures."""


class InvalidNicknameError(ValidationError):
    """Raised when a nickname format is invalid."""

    def __init__(self, nickname: str) -> None:
        self.nickname = nickname
        super().__init__(f"Invalid nickname: {nickname!r}. Must match [a-zA-Z0-9_]+")


class InvalidEmailError(ValidationError):
    """Raised when email format is invalid."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Invalid email: {email!r}")


class InvalidTitleError(ValidationError):
    """Raised when text title is invalid."""


class InvalidSnapshotLabelError(ValidationError):
    """Raised when snapshot label format is invalid."""


# === Not Found Errors ===
class NotFoundError(McodexError, LookupError):
    """Base for resource not found errors."""


class RepoConfigNotFoundError(NotFoundError, FileNotFoundError):
    """Raised when no `.mcodex/config.yaml` can be found."""

    def __init__(self) -> None:
        super().__init__(
            "No .mcodex/config.yaml found. Run `mcodex init` in a Git repo first."
        )


@dataclass(frozen=True)
class AuthorNotFoundError(NotFoundError):
    """Raised when requested author doesn't exist."""

    nickname: str

    def __str__(self) -> str:
        return f"Author not found: {self.nickname!r}"


@dataclass(frozen=True)
class AuthorAlreadyExistsError(ValidationError):
    """Raised when trying to add duplicate author."""

    nickname: str

    def __str__(self) -> str:
        return f"Author '{self.nickname}' already exists."


@dataclass(frozen=True)
class PipelineNotFoundError(NotFoundError):
    """Raised when requested pipeline doesn't exist."""

    requested: str
    available: tuple[str, ...]

    def __str__(self) -> str:
        if not self.available:
            return f"Pipeline '{self.requested}' not found."
        options = ", ".join(self.available)
        return f"Pipeline '{self.requested}' not found. Available: {options}."


# === Infrastructure Errors ===
class InfrastructureError(McodexError, RuntimeError):
    """Base for external tool/system failures."""


class GitOperationError(InfrastructureError):
    """Raised when a git command fails."""

    def __init__(self, operation: str, stdout: str, stderr: str) -> None:
        self.operation = operation
        self.stdout = stdout
        self.stderr = stderr
        msg = f"Git {operation} failed:\n{stderr or stdout}"
        super().__init__(msg)


class GitRepoNotFoundError(GitOperationError):
    """Raised when git repository is not found."""

    def __init__(self) -> None:
        super().__init__("", "", "")

    def __str__(self) -> str:
        return "Git repository not found"


class BuildToolError(InfrastructureError):
    """Raised when pandoc/latexmk/vlna fails."""

    def __init__(self, tool: str, returncode: int, output: str) -> None:
        self.tool = tool
        self.returncode = returncode
        self.output = output
        super().__init__(f"{tool} failed with code {returncode}:\n{output}")


# === Configuration Errors ===
class ConfigurationError(McodexError, ValueError):
    """Base for configuration problems."""


class PipelineConfigError(ConfigurationError):
    """Raised when pipeline configuration is invalid."""
