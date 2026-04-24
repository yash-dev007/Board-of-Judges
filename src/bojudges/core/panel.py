from __future__ import annotations

from dataclasses import dataclass

from bojudges.core.router import RouteResult
from bojudges.judges.base import Judge


@dataclass
class PanelItem:
    judge: Judge
    score: float
    reason: str


class PanelSelector:
    """Deterministic ranker: picks the top-K judges given a route.

    Score = tag_overlap(judge.tags, route.domain_tags)
          + 2 * risk_overlap(judge.risk_tags, route.risk_tags)
          + sensitivity_bonus
          + tier_bias (Tier 1 judges get a small bump so they lead panels)
    Tie-breaks: higher tier (lower number) wins; then alphabetical id.
    """

    def __init__(self, max_judges: int = 10) -> None:
        self.max_judges = max_judges

    def select(
        self,
        judges: list[Judge],
        route: RouteResult,
        panel_filter: list[str] | None = None,
        solo: str | None = None,
        allow_all: bool = False,
    ) -> list[PanelItem]:
        if solo:
            for j in judges:
                if j.id == solo or solo in j.id or j.name.lower() == solo.lower():
                    return [PanelItem(judge=j, score=1.0, reason="solo selection")]
            return []

        scored: list[PanelItem] = []
        for j in judges:
            if panel_filter and not any(p in j.tags for p in panel_filter):
                continue
            s, reason = self._score(j, route)
            if s <= 0:
                continue
            scored.append(PanelItem(judge=j, score=s, reason=reason))

        scored.sort(key=lambda x: (-x.score, x.judge.tier, x.judge.id))

        if allow_all:
            return scored
        return scored[: self.max_judges]

    @staticmethod
    def _score(judge: Judge, route: RouteResult) -> tuple[float, str]:
        tag_overlap = len(set(judge.tags) & set(route.domain_tags))
        risk_overlap = len(set(judge.risk_tags) & set(route.risk_tags))
        if tag_overlap == 0 and risk_overlap == 0:
            return 0.0, "no tag or risk overlap"
        tier_bias = (5 - judge.tier) * 0.25
        sens_bonus = 0.5 if route.sensitivity == "high" and "security" in judge.tags else 0.0
        score = tag_overlap + 2 * risk_overlap + tier_bias + sens_bonus
        reason = (
            f"tags={tag_overlap} risks={risk_overlap} tier={judge.tier} "
            f"sens={route.sensitivity}"
        )
        return score, reason
