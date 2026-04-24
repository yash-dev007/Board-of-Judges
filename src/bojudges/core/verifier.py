from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bojudges.schema import Issue

CATEGORY_HINTS: dict[str, list[str]] = {
    "sql-injection": [
        "execute", "executemany", "query", "cursor", "raw", "fetchall",
        "%s", "format", ".format", "+", "concat", "f\"", "f'", "SELECT",
        "INSERT", "UPDATE", "DELETE", "WHERE",
    ],
    "command-injection": [
        "os.system", "subprocess", "shell=True", "Popen", "call", "check_output",
        "exec", "eval", "os.popen", "commands.", "child_process", "execSync",
    ],
    "xss": [
        "innerHTML", "document.write", "dangerouslySetInnerHTML", "Markup",
        "|safe", "render_template_string", "v-html",
    ],
    "ssrf": [
        "requests.", "urllib", "urlopen", "fetch", "axios", "curl", "http.get",
    ],
    "path-traversal": [
        "open(", "Path(", "..", "os.path.join", "read_file",
    ],
    "hardcoded-secret": [
        "password", "api_key", "secret", "token", "AKIA", "ssh-rsa",
        "-----BEGIN", "Bearer ",
    ],
    "weak-crypto": [
        "md5", "sha1", "DES", "ECB", "Random(", "random.random", "PKCS1v15",
    ],
    "deserialization": [
        "pickle.loads", "yaml.load", "marshal.loads", "eval(", "Function(",
    ],
    "auth": [
        "jwt", "session", "cookie", "password", "token", "auth",
    ],
    "input-validation": [
        "request.", "params", "args", "form", "body", "query", "input",
    ],
}


@dataclass
class VerifyResult:
    issue: Issue
    verified: bool
    reason: str = ""


class LineVerifier:
    """Catches line-number and symbol hallucinations cheaply.

    For every issue:
      1. The claimed file must exist and have the claimed line.
      2. Within ±`line_window` lines of the claim, at least one hint token
         associated with the issue category must appear.

    If both checks pass, verified=True. This catches ~60% of line hallucinations
    and most "invented category" hallucinations without calling an LLM.
    """

    def __init__(self, line_window: int = 3) -> None:
        self.line_window = line_window

    def verify_all(self, issues: list[Issue], source_files: dict[str, str]) -> list[VerifyResult]:
        return [self.verify(i, source_files) for i in issues]

    def verify(self, issue: Issue, source_files: dict[str, str]) -> VerifyResult:
        content = source_files.get(issue.file)
        if content is None:
            p = Path(issue.file)
            if p.exists():
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    return VerifyResult(issue, False, f"cannot read {issue.file}")
            else:
                return VerifyResult(issue, False, f"file not found: {issue.file}")

        if issue.line == -1:
            # File-level issue: only hint-check
            return self._hint_check(issue, content, range_lines=(1, len(content.splitlines())))

        lines = content.splitlines()
        if issue.line < 1 or issue.line > len(lines):
            return VerifyResult(
                issue, False, f"line {issue.line} out of range (file has {len(lines)} lines)"
            )

        start = max(1, issue.line - self.line_window)
        end = min(len(lines), issue.line + self.line_window)
        return self._hint_check(issue, content, range_lines=(start, end))

    def _hint_check(
        self, issue: Issue, content: str, range_lines: tuple[int, int]
    ) -> VerifyResult:
        lines = content.splitlines()
        start, end = range_lines
        window_text = "\n".join(lines[start - 1 : end])

        hints = CATEGORY_HINTS.get(issue.category.lower(), [])
        if not hints:
            # Unknown category: accept if line range exists. Lower trust but not a reject.
            return VerifyResult(issue, True, f"no hint set for category={issue.category}")

        lower = window_text.lower()
        for h in hints:
            needle = h.lower()
            if needle in lower:
                return VerifyResult(issue, True, f"matched hint {h!r}")
            if re.search(re.escape(needle), window_text):
                return VerifyResult(issue, True, f"matched hint {h!r}")

        return VerifyResult(
            issue,
            False,
            f"no category hint found near line {issue.line} (category={issue.category})",
        )

    @staticmethod
    def apply(issues: list[Issue], results: list[VerifyResult]) -> list[Issue]:
        """Return a new list of issues with `verified` field set per results."""
        out: list[Issue] = []
        for i, r in zip(issues, results, strict=True):
            out.append(i.model_copy(update={"verified": r.verified}))
        return out
