from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bojudges.schema import (
    BoardReport,
    Issue,
    JudgeVerdict,
    RunManifest,
    Severity,
    SubmissionRef,
    Synthesis,
    Verdict,
)


def test_issue_round_trip():
    i = Issue(
        id="j1:0",
        severity=Severity.HIGH,
        title="sqli",
        description="string concat into cursor.execute",
        file="x.py",
        line=5,
        category="sql-injection",
        cwe="CWE-89",
        confidence=0.9,
    )
    dumped = i.model_dump_json()
    restored = Issue.model_validate_json(dumped)
    assert restored == i


def test_issue_rejects_bad_line():
    with pytest.raises(Exception):
        Issue(
            id="x",
            severity=Severity.LOW,
            title="t",
            description="d",
            file="f",
            line=-5,
            category="x",
            confidence=0.5,
        )


def test_issue_rejects_end_before_start():
    with pytest.raises(Exception):
        Issue(
            id="x",
            severity=Severity.LOW,
            title="t",
            description="d",
            file="f",
            line=10,
            end_line=5,
            category="x",
            confidence=0.5,
        )


def test_manifest_fingerprint_stable():
    m1 = RunManifest(
        bojudges_version="0.2.0",
        models={"judge-a": "claude-sonnet-4-6"},
        temperature=0.3,
        seed=42,
        prompt_hashes={"judge-a": "abc123"},
    )
    m2 = RunManifest(
        bojudges_version="0.2.0",
        models={"judge-a": "claude-sonnet-4-6"},
        temperature=0.3,
        seed=42,
        prompt_hashes={"judge-a": "abc123"},
        created_at=datetime(2030, 1, 1, tzinfo=UTC),
    )
    # Timestamp must not affect fingerprint.
    assert m1.fingerprint() == m2.fingerprint()


def test_manifest_fingerprint_changes_with_prompt():
    base = dict(
        bojudges_version="0.2.0",
        models={"judge-a": "claude-sonnet-4-6"},
        temperature=0.3,
        seed=42,
    )
    m1 = RunManifest(**base, prompt_hashes={"judge-a": "aaa"})
    m2 = RunManifest(**base, prompt_hashes={"judge-a": "bbb"})
    assert m1.fingerprint() != m2.fingerprint()


def test_board_report_serializes():
    verdict = JudgeVerdict(
        judge_id="j",
        judge_name="Test Judge",
        tier=1,
        verdict=Verdict.PASS,
        score=8.0,
        confidence=0.8,
        core_finding="nothing wrong",
        duration_ms=100,
        tokens_in=500,
        tokens_out=100,
        cost_usd=0.01,
        model_id="mock",
        prompt_hash="abc",
    )
    synthesis = Synthesis(
        board_verdict=Verdict.PASS,
        board_score=8.0,
        consensus="looks fine",
        recommended_action="ship it",
    )
    manifest = RunManifest(
        bojudges_version="0.2.0",
        models={"j": "mock"},
        temperature=0.3,
    )
    report = BoardReport(
        submission=SubmissionRef(path="x.py", sha256="abc", size_bytes=10),
        judges=[verdict],
        synthesis=synthesis,
        manifest=manifest,
    )
    js = report.pretty_json()
    assert '"verdict":' in js
    assert '"schema_version":' in js
