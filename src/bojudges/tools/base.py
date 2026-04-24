from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ToolUnavailable(RuntimeError):
    """Raised when an external tool is not installed or runnable."""


@dataclass
class Finding:
    """Normalized output from any static-analysis tool."""

    tool: str
    rule_id: str
    message: str
    file: str
    line: int
    end_line: int | None = None
    severity: str = "warning"
    cwe: str | None = None
    category: str = ""
    snippet: str = ""
    raw: dict = field(default_factory=dict)

    def citation(self) -> str:
        return f"{self.tool}:{self.rule_id}@{self.file}:{self.line}"


class Tool(ABC):
    name: str = "base"
    version: str = "0.0.0"

    @abstractmethod
    def available(self) -> bool:
        """Return True if tool can run on this system."""

    @abstractmethod
    def run(self, file_path: str, content: str) -> list[Finding]:
        """Run the tool and return normalized findings."""

    def describe(self) -> str:
        return f"{self.name} ({'available' if self.available() else 'unavailable'})"
