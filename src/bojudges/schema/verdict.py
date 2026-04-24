from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Verdict(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


class Severity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Issue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable ID for dedup across judges")
    severity: Severity
    title: str = Field(max_length=200)
    description: str = Field(max_length=4000)
    file: str
    line: int = Field(ge=-1, description="1-indexed source line; -1 = file-level")
    end_line: int | None = Field(default=None, ge=1)
    cwe: str | None = Field(default=None, description="e.g. 'CWE-89'")
    category: str = Field(description="e.g. 'sql-injection', 'command-injection'")
    fix_hint: str | None = Field(default=None, max_length=2000)
    tool_source: Literal["semgrep", "bandit", "ruff", "eslint", "tsc", "ast", "llm", "hybrid"] = "llm"
    confidence: float = Field(ge=0.0, le=1.0)
    tool_citations: list[str] = Field(default_factory=list)
    verified: bool = Field(default=False, description="Line+symbol verifier passed")

    @field_validator("end_line")
    @classmethod
    def _end_after_start(cls, v: int | None, info) -> int | None:
        if v is not None and "line" in info.data and info.data["line"] > 0 and v < info.data["line"]:
            raise ValueError("end_line must be >= line")
        return v


class JudgeVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    judge_id: str
    judge_name: str
    tier: int = Field(ge=1, le=4)
    verdict: Verdict
    score: float = Field(ge=0.0, le=10.0)
    confidence: float = Field(ge=0.0, le=1.0, description="Calibrated if judge is on eval set")
    confidence_calibrated: bool = False
    core_finding: str = Field(max_length=400)
    issues: list[Issue] = Field(default_factory=list)
    tools_run: list[str] = Field(default_factory=list)
    duration_ms: int = Field(ge=0)
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0, default=0)
    cache_create_tokens: int = Field(ge=0, default=0)
    cost_usd: float = Field(ge=0.0)
    model_id: str
    prompt_hash: str
    exemplars_hash: str = ""
    error: str | None = None


class Synthesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    board_verdict: Verdict
    board_score: float = Field(ge=0.0, le=10.0)
    critical_issues: list[str] = Field(default_factory=list, description="Human-readable summaries")
    warnings: list[str] = Field(default_factory=list)
    consensus: str
    disagreements: list[str] = Field(
        default_factory=list,
        description="Points where judges materially disagree; surfaced, not collapsed",
    )
    recommended_action: str


class SubmissionRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str
    size_bytes: int
    language: str | None = None
    loc: int | None = None


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    bojudges_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    models: dict[str, str] = Field(default_factory=dict, description="role -> model_id")
    temperature: float
    seed: int | None = None
    prompt_hashes: dict[str, str] = Field(default_factory=dict, description="judge_id -> prompt_hash")
    exemplars_hashes: dict[str, str] = Field(default_factory=dict, description="judge_id -> exemplars_hash")
    tools_versions: dict[str, str] = Field(default_factory=dict, description="tool_name -> version")
    total_cost_usd: float = 0.0
    total_duration_ms: int = 0

    def fingerprint(self) -> str:
        import hashlib
        import json

        payload = {
            "schema_version": self.schema_version,
            "bojudges_version": self.bojudges_version,
            "models": self.models,
            "temperature": self.temperature,
            "seed": self.seed,
            "prompt_hashes": self.prompt_hashes,
            "exemplars_hashes": self.exemplars_hashes,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


class BoardReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submission: SubmissionRef
    judges: list[JudgeVerdict]
    synthesis: Synthesis
    manifest: RunManifest

    def pretty_json(self) -> str:
        return self.model_dump_json(indent=2)
