from __future__ import annotations

from bojudges.core.dispatcher import DispatchConfig, Dispatcher
from bojudges.core.panel import PanelItem
from bojudges.core.verifier import LineVerifier
from bojudges.judges.base import Judge, JudgeContext
from bojudges.providers.base import Provider, ToolCall
from bojudges.providers.mock import MockProvider, ScriptedResponse
from bojudges.schema import Verdict


class _StubJudge(Judge):
    id = "stub-judge"
    name = "Stub Judge"
    tier = 1
    tags = ["security"]

    def persona_prompt(self) -> str:
        return "you are stub judge"


def _provider() -> Provider:
    return MockProvider(
        default_response=ScriptedResponse(
            text=None,
            tool_calls=[
                ToolCall(
                    id="t1",
                    name="record_verdict",
                    input={
                        "verdict": "PASS",
                        "score": 9,
                        "confidence": 0.9,
                        "core_finding": "nothing found",
                        "issues": [],
                    },
                )
            ],
        )
    )


def test_dispatcher_runs_judge_returns_valid_verdict():
    judge = _StubJudge()
    item = PanelItem(judge=judge, score=1.0, reason="test")
    ctx = JudgeContext(
        submission_path="nope.py",
        submission_content="print('hello')",
        language="python",
    )

    disp = Dispatcher(
        provider_factory=lambda _: _provider(),
        verifier=LineVerifier(),
        config=DispatchConfig(max_workers=1),
    )
    verdicts = disp.dispatch([item], ctx)
    assert len(verdicts) == 1
    assert verdicts[0].verdict == Verdict.PASS
    assert verdicts[0].score == 9.0
    assert verdicts[0].judge_id == "stub-judge"
    assert verdicts[0].duration_ms >= 0


def test_dispatcher_parallel_across_multiple_judges():
    judges = [_StubJudge() for _ in range(3)]
    for i, j in enumerate(judges):
        j.id = f"stub-{i}"
        j.name = f"Stub {i}"
    items = [PanelItem(judge=j, score=1.0, reason="t") for j in judges]
    ctx = JudgeContext(
        submission_path="nope.py", submission_content="x=1", language="python"
    )
    disp = Dispatcher(
        provider_factory=lambda _: _provider(),
        config=DispatchConfig(max_workers=3),
    )
    verdicts = disp.dispatch(items, ctx)
    assert len(verdicts) == 3
    ids = {v.judge_id for v in verdicts}
    assert ids == {"stub-0", "stub-1", "stub-2"}


def test_dispatcher_handles_provider_error():
    def bad_factory(_):
        raise RuntimeError("no provider available")

    disp = Dispatcher(provider_factory=bad_factory)
    ctx = JudgeContext(submission_path="x.py", submission_content="x=1")
    judge = _StubJudge()
    items = [PanelItem(judge=judge, score=1.0, reason="t")]
    verdicts = disp.dispatch(items, ctx)
    assert len(verdicts) == 1
    assert verdicts[0].verdict == Verdict.SKIP
    assert verdicts[0].error
