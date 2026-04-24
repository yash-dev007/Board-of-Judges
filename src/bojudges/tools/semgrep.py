from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from bojudges.tools.base import Finding, Tool

_SEVERITY_MAP = {
    "INFO": "info",
    "WARNING": "warning",
    "ERROR": "error",
}


class SemgrepTool(Tool):
    """Thin wrapper around the `semgrep` CLI.

    Gracefully degrades: if semgrep is not installed, `available()` returns False
    and callers should treat tool-grounded judges as pure-LLM (with lower
    confidence). This is a feature, not a bug — the project shouldn't hard-fail
    for users who can't or won't install semgrep.
    """

    name = "semgrep"

    def __init__(self, configs: list[str] | None = None, timeout_sec: int = 60) -> None:
        self.configs = configs or [
            "p/security-audit",
            "p/sql-injection",
            "p/command-injection",
            "p/owasp-top-ten",
        ]
        self.timeout_sec = timeout_sec

    def available(self) -> bool:
        return shutil.which("semgrep") is not None

    def run(self, file_path: str, content: str) -> list[Finding]:
        if not self.available():
            return []

        path = Path(file_path)
        if not path.exists():
            return []

        args = ["semgrep", "scan", "--json", "--quiet", "--error", "--no-git-ignore"]
        for cfg in self.configs:
            args += ["--config", cfg]
        args.append(str(path))

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
                check=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

        if not result.stdout:
            return []

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        findings: list[Finding] = []
        for r in data.get("results", []):
            extra = r.get("extra") or {}
            metadata = extra.get("metadata") or {}
            cwe_raw = metadata.get("cwe")
            if isinstance(cwe_raw, list):
                cwe: str | None = cwe_raw[0] if cwe_raw else None
            else:
                cwe = cwe_raw

            findings.append(
                Finding(
                    tool=self.name,
                    rule_id=r.get("check_id", "unknown"),
                    message=extra.get("message", "").strip(),
                    file=r.get("path", str(path)),
                    line=int(r.get("start", {}).get("line", 0) or 0),
                    end_line=int(r.get("end", {}).get("line", 0) or 0) or None,
                    severity=_SEVERITY_MAP.get(
                        str(extra.get("severity", "")).upper(), "warning"
                    ),
                    cwe=_normalize_cwe(cwe),
                    category=_pick_category(metadata, r.get("check_id", "")),
                    snippet=(extra.get("lines") or "").strip()[:500],
                    raw=r,
                )
            )
        return findings

    def _version(self) -> str:
        if not self.available():
            return ""
        try:
            r = subprocess.run(
                ["semgrep", "--version"], capture_output=True, text=True, timeout=5
            )
            return (r.stdout or "").strip()
        except Exception:
            return ""


def _normalize_cwe(cwe_raw: str | None) -> str | None:
    if not cwe_raw:
        return None
    s = str(cwe_raw).strip()
    if s.upper().startswith("CWE-"):
        return s.upper().split(":", 1)[0]
    if s.isdigit():
        return f"CWE-{s}"
    return s


def _pick_category(metadata: dict, rule_id: str) -> str:
    cat = metadata.get("category") or ""
    if cat:
        return str(cat).lower()
    rid = rule_id.lower()
    if "sql" in rid:
        return "sql-injection"
    if "command" in rid or "shell" in rid:
        return "command-injection"
    if "xss" in rid:
        return "xss"
    if "ssrf" in rid:
        return "ssrf"
    return "security"
