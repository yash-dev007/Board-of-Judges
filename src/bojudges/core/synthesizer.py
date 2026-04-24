from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter

from bojudges.schema import JudgeVerdict, Severity, Synthesis, Verdict


class Synthesizer(ABC):
    @abstractmethod
    def synthesize(self, verdicts: list[JudgeVerdict]) -> Synthesis: ...


class RuleBasedSynthesizer(Synthesizer):
    """Deterministic synthesis — zero LLM cost, fully reproducible.

    Board verdict:
      - FAIL if any verified CRITICAL or HIGH issue exists anywhere
      - WARN if any verified MEDIUM issue, or any judge voted WARN/FAIL
      - PASS otherwise
    Board score: average of judge scores weighted by calibrated confidence.
    """

    SEVERITY_RANK = {
        Severity.CRITICAL: 5,
        Severity.HIGH: 4,
        Severity.MEDIUM: 3,
        Severity.LOW: 2,
        Severity.INFO: 1,
    }

    def synthesize(self, verdicts: list[JudgeVerdict]) -> Synthesis:
        active = [v for v in verdicts if v.verdict != Verdict.SKIP]
        if not active:
            return Synthesis(
                board_verdict=Verdict.SKIP,
                board_score=0.0,
                critical_issues=[],
                warnings=[],
                consensus="No judges produced a valid verdict.",
                disagreements=[],
                recommended_action="Re-run after resolving judge errors.",
            )

        all_issues = [(v, issue) for v in active for issue in v.issues]
        verified = [(v, i) for v, i in all_issues if i.verified]

        crit_issues = [
            f"[{v.judge_name}] {i.title} ({i.file}:{i.line}) — {i.category}"
            for v, i in verified
            if i.severity in (Severity.CRITICAL, Severity.HIGH)
        ]
        warn_issues = [
            f"[{v.judge_name}] {i.title} ({i.file}:{i.line}) — {i.category}"
            for v, i in verified
            if i.severity == Severity.MEDIUM
        ]

        votes = Counter(v.verdict for v in active)
        if crit_issues:
            board_verdict = Verdict.FAIL
        elif warn_issues or votes[Verdict.FAIL] or votes[Verdict.WARN]:
            board_verdict = Verdict.WARN
        else:
            board_verdict = Verdict.PASS

        weighted_sum = 0.0
        weight_total = 0.0
        for v in active:
            w = max(v.confidence, 0.1)
            weighted_sum += v.score * w
            weight_total += w
        board_score = weighted_sum / weight_total if weight_total else 0.0

        consensus = self._consensus_text(active, votes)
        disagreements = self._disagreement_text(active, all_issues)
        action = self._action_text(board_verdict, crit_issues, warn_issues)

        return Synthesis(
            board_verdict=board_verdict,
            board_score=round(board_score, 2),
            critical_issues=crit_issues,
            warnings=warn_issues,
            consensus=consensus,
            disagreements=disagreements,
            recommended_action=action,
        )

    @staticmethod
    def _consensus_text(active: list[JudgeVerdict], votes: Counter) -> str:
        parts = [f"{count} {v.value}" for v, count in votes.most_common()]
        top_finding = max(active, key=lambda x: (x.verdict != Verdict.PASS, -x.score))
        return f"Votes: {', '.join(parts)}. Lead concern: {top_finding.core_finding}"

    @staticmethod
    def _disagreement_text(
        active: list[JudgeVerdict], all_issues
    ) -> list[str]:
        out: list[str] = []
        votes = Counter(v.verdict for v in active)
        if len(votes) >= 2 and votes.most_common(1)[0][1] < len(active):
            tally = ", ".join(f"{c} {v.value}" for v, c in votes.most_common())
            out.append(f"Verdict split: {tally}")

        by_category: dict[str, list[tuple[str, bool]]] = {}
        for v, i in all_issues:
            by_category.setdefault(i.category, []).append((v.judge_name, i.verified))
        for cat, entries in by_category.items():
            if len(entries) >= 2 and any(e[1] for e in entries) and any(not e[1] for e in entries):
                out.append(f"Category {cat!r} has mixed verification across judges")

        return out

    @staticmethod
    def _action_text(verdict: Verdict, crits: list[str], warns: list[str]) -> str:
        if verdict == Verdict.FAIL:
            return f"Fix {len(crits)} critical issue(s) before merging. Re-run board after."
        if verdict == Verdict.WARN:
            return f"Address {len(warns)} warning(s); ship at your discretion."
        return "Looks good. No blocking issues found by the calibrated judges."
