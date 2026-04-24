from __future__ import annotations

from bojudges.core.panel import PanelSelector
from bojudges.core.router import RouteResult
from bojudges.judges.base import Judge


class _FakeJudge(Judge):
    def __init__(self, jid: str, tier: int, tags: list[str], risk_tags: list[str] | None = None):
        super().__init__()
        self.id = jid
        self.name = jid.replace("-", " ").title()
        self.tier = tier
        self.tags = tags
        self.risk_tags = risk_tags or []

    def persona_prompt(self) -> str:
        return "you are " + self.id


def _route() -> RouteResult:
    return RouteResult(
        language="python",
        domain_tags=["security", "backend", "code"],
        risk_tags=["sql-injection"],
        loc=10,
        sensitivity="high",
    )


def test_select_top_k():
    judges = [
        _FakeJudge("sec-a", 1, ["security", "code"], ["sql-injection"]),
        _FakeJudge("eng-a", 1, ["backend", "code"]),
        _FakeJudge("ai-a", 2, ["ai"]),  # no overlap
        _FakeJudge("qa-a", 3, ["testing"]),  # no overlap
    ]
    selector = PanelSelector(max_judges=10)
    items = selector.select(judges, _route())
    ids = [i.judge.id for i in items]
    assert "sec-a" in ids
    assert "eng-a" in ids
    assert "ai-a" not in ids  # zero overlap => dropped
    assert ids[0] == "sec-a"  # security outranks because of risk overlap


def test_panel_filter():
    judges = [
        _FakeJudge("sec-a", 1, ["security", "code"], ["sql-injection"]),
        _FakeJudge("eng-a", 1, ["backend", "code"]),
    ]
    items = PanelSelector().select(judges, _route(), panel_filter=["security"])
    assert [i.judge.id for i in items] == ["sec-a"]


def test_solo():
    judges = [
        _FakeJudge("sec-a", 1, ["security"]),
        _FakeJudge("eng-a", 1, ["backend"]),
    ]
    items = PanelSelector().select(judges, _route(), solo="eng-a")
    assert [i.judge.id for i in items] == ["eng-a"]


def test_max_cap():
    judges = [_FakeJudge(f"j{i}", 1, ["code"]) for i in range(20)]
    items = PanelSelector(max_judges=5).select(judges, _route())
    assert len(items) == 5


def test_all_flag_removes_cap():
    judges = [_FakeJudge(f"j{i}", 1, ["code"]) for i in range(20)]
    items = PanelSelector(max_judges=5).select(judges, _route(), allow_all=True)
    assert len(items) == 20
