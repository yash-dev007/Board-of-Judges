from __future__ import annotations

from pathlib import Path

from evals.runner import aggregate, load_dataset, score_case

from bojudges.judges import load_builtin_judges
from bojudges.judges.base import JudgeContext


def test_seed_dataset_loads():
    ds = Path(__file__).parent.parent / "evals" / "datasets" / "sqli_seed"
    gt, cases = load_dataset(ds)
    assert gt["dataset"] == "sqli_seed"
    assert len(cases) == 10
    assert sum(1 for c in cases if c.expected_verdict == "FAIL") == 5
    assert sum(1 for c in cases if c.expected_verdict == "PASS") == 5


def test_eval_harness_with_mock_provider_hits_gate():
    """Wire up MockProvider that always returns the ground-truth answer.
    This proves the pipeline plumbs end-to-end; does NOT validate the LLM.
    """
    from evals.runner import mock_provider_for

    from bojudges.core.verifier import LineVerifier

    ds = Path(__file__).parent.parent / "evals" / "datasets" / "sqli_seed"
    _, cases = load_dataset(ds)

    judge = load_builtin_judges().by_id("sec-appsec-injection")
    assert judge is not None

    provider = mock_provider_for(cases)
    verifier = LineVerifier()

    results = []
    for case in cases:
        ctx = JudgeContext(
            submission_path=str(case.path),
            submission_content=case.content,
            language=case.language,
        )
        verdict = judge.review(provider=provider, ctx=ctx, verifier=verifier)
        results.append(score_case(case, verdict))

    metrics = aggregate(results)

    # Mock provider returns ground truth, so the pipeline itself (prompt
    # building, verifier, scoring) should hit the Phase 0 gate perfectly.
    assert metrics["precision"] >= 0.70
    assert metrics["recall"] >= 0.60
    assert metrics["ece"] <= 0.15
    assert metrics["errored"] == 0
