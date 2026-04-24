from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RouteResult:
    language: str
    domain_tags: list[str]
    risk_tags: list[str]
    loc: int
    sensitivity: str


LANG_BY_EXT: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
    ".kt": "kotlin",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".sql": "sql",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".tf": "terraform",
    ".sol": "solidity",
    ".sh": "shell",
    ".ps1": "powershell",
    ".dockerfile": "dockerfile",
}

TAGS_BY_LANG: dict[str, list[str]] = {
    "python": ["backend", "security", "testing", "performance", "code"],
    "typescript": ["frontend", "accessibility", "security", "testing", "ui", "code"],
    "javascript": ["frontend", "accessibility", "security", "testing", "ui", "code"],
    "go": ["backend", "concurrency", "security", "testing", "performance", "code"],
    "rust": ["backend", "security", "performance", "systems", "code"],
    "ruby": ["backend", "security", "testing", "code"],
    "java": ["backend", "security", "testing", "performance", "code"],
    "kotlin": ["backend", "mobile", "security", "code"],
    "cpp": ["systems", "performance", "security", "memory-safety", "code"],
    "c": ["systems", "performance", "security", "memory-safety", "code"],
    "sql": ["database", "security", "backend", "performance"],
    "yaml": ["devops", "security", "infrastructure", "cicd"],
    "terraform": ["devops", "security", "infrastructure", "cloud"],
    "solidity": ["blockchain", "security", "legal"],
    "dockerfile": ["devops", "security", "infrastructure", "containerization"],
    "markdown": ["product", "docs", "strategy"],
}


class Router:
    """Classifies a submission. Deterministic; no LLM by default.

    Optionally accepts a provider for harder cases (ambiguous `.yaml`, large
    markdown files) but that is Phase 1+. Phase 0 is rule-based only.
    """

    def __init__(self) -> None:
        pass

    def route(self, file_path: str, content: str | None = None) -> RouteResult:
        p = Path(file_path)
        ext = p.suffix.lower()
        language = LANG_BY_EXT.get(ext, "unknown")
        if p.name.lower() == "dockerfile":
            language = "dockerfile"

        if content is None:
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                content = ""

        loc = len([ln for ln in content.splitlines() if ln.strip()])
        domain_tags = list(TAGS_BY_LANG.get(language, ["code"]))
        risk_tags = self._risk_tags(language, content)
        sensitivity = self._sensitivity(language, content)

        return RouteResult(
            language=language,
            domain_tags=domain_tags,
            risk_tags=risk_tags,
            loc=loc,
            sensitivity=sensitivity,
        )

    @staticmethod
    def _risk_tags(language: str, content: str) -> list[str]:
        tags: list[str] = []
        lower = content.lower()
        risk_patterns = {
            "sql-injection": ["execute(", "executemany(", "cursor.", ".raw(", "format(", "% ("],
            "command-injection": ["os.system", "subprocess.", "shell=true", "child_process", "exec("],
            "crypto": ["aes", "rsa", "hashlib", "crypto", "hmac", "cipher"],
            "auth": ["jwt", "password", "login", "session", "cookie", "bcrypt", "argon2"],
            "net": ["requests.", "urllib", "http.", "fetch(", "axios"],
            "secrets": ["api_key", "secret", "password", "token"],
            "serialization": ["pickle.", "yaml.load", "json.loads", "marshal.", "eval("],
        }
        for tag, needles in risk_patterns.items():
            if any(n in lower for n in needles):
                tags.append(tag)
        return tags

    @staticmethod
    def _sensitivity(language: str, content: str) -> str:
        lower = content.lower()
        if any(
            n in lower
            for n in ("password", "api_key", "secret", "jwt", "session", "auth")
        ):
            return "high"
        if language in ("sql", "terraform", "dockerfile"):
            return "high"
        return "normal"
