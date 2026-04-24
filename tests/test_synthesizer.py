from __future__ import annotations

from bojudges.core.synthesizer import RuleBasedSynthesizer
from bojudges.schema import Issue, JudgeVerdict, Severity, Verdict


def _verdict(
    jid: str,
    v: Verdict,
    score: float,
    issues: list[Issue] | None = None,
    conf: float = 0.8,
) -> JudgeVerdict:
    return JudgeVerdict(
        judge_id=jid,
        judge_name=jid.title(),
        tier=1,
        verdict=v,
        score=score,
        confidence=conf,
        core_finding=f"{jid} finding",
        issues=issues or [],
        duration_ms=10,
        tokens_in=100,
        tokens_out=50,
        cost_usd=0.01,
        model_id="mock",
        prompt_hash="h",
    )


def _issue(sev: Severity, category: str = "sql-injection", verified: bool = True) -> Issue:
    return Issue(
        id="t:0",
        severity=sev,
        title="t",
        description="d",
        file="f",
        line=1,
        category=category,
        confidence=0.9,
        verified=verified,
    )


def test_synth_all_pass_returns_pass():
    verdicts = [_verdict("a", Verdict.PASS, 9), _verdict("b", Verdict.PASS, 8)]
    s = RuleBasedSynthesizer().synthesize(verdicts)
    assert s.board_verdict == Verdict.PASS
    assert s.critical_issues == []


def test_synth_verified_critical_yields_fail():
    verdicts = [
        _verdict("a", Verdict.FAIL, 2, [_issue(Severity.CRITICAL)]),
        _verdict("b", Verdict.PASS, 8),
    ]
    s = RuleBasedSynthesizer().synthesize(verdicts)
    assert s.board_verdict == Verdict.FAIL
    assert len(s.critical_issues) == 1


def test_synth_unverified_critical_does_not_trigger_fail():
    verdicts = [
        _verdict("a", Verdict.WARN, 4, [_issue(Severity.CRITICAL, verified=False)]),
    ]
    s = RuleBasedSynthesizer().synthesize(verdicts)
    # Unverified issue should NOT raise to FAIL
    assert s.board_verdict == Verdict.WARN
    assert s.critical_issues == []


def test_synth_disagreement_surfaced():
    verdicts = [
        _verdict("a", Verdict.PASS, 9),
        _verdict("b", Verdict.PASS, 8),
        _verdict("c", Verdict.FAIL, 2, [_issue(Severity.HIGH)]),
    ]
    s = RuleBasedSynthesizer().synthesize(verdicts)
    assert any("split" in d.lower() for d in s.disagreements)


def test_synth_all_skip_is_skip():
    verdicts = [_verdict("a", Verdict.SKIP, 0)]
    s = RuleBasedSynthesizer().synthesize(verdicts)
    assert s.board_verdict == Verdict.SKIP
