from __future__ import annotations

from bojudges.schema import BoardReport, JudgeVerdict, Verdict

_VERDICT_ICON = {
    Verdict.PASS: "PASS",
    Verdict.WARN: "WARN",
    Verdict.FAIL: "FAIL",
    Verdict.SKIP: "SKIP",
}


def report_to_markdown(report: BoardReport) -> str:
    lines: list[str] = []
    lines.append(f"# Board of Judges — `{report.submission.path}`")
    lines.append("")
    s = report.synthesis
    lines.append(f"**Board verdict:** `{s.board_verdict.value}`  |  **Score:** {s.board_score:.1f} / 10")
    lines.append("")

    lines.append("| Tier | Judge | Verdict | Score | Conf | Issues | Duration |")
    lines.append("|---:|---|:-:|---:|---:|---:|---:|")
    for v in report.judges:
        verified = sum(1 for i in v.issues if i.verified)
        lines.append(
            f"| {v.tier} | {v.judge_name} | {_VERDICT_ICON[v.verdict]} | "
            f"{v.score:.1f} | {v.confidence:.2f} | {verified} | {v.duration_ms} ms |"
        )
    lines.append("")

    if s.critical_issues:
        lines.append("## Critical issues")
        for x in s.critical_issues:
            lines.append(f"- {x}")
        lines.append("")
    if s.warnings:
        lines.append("## Warnings")
        for x in s.warnings:
            lines.append(f"- {x}")
        lines.append("")
    if s.disagreements:
        lines.append("## Disagreements")
        lines.append("Surfaced intentionally — not collapsed into a fake consensus.")
        for x in s.disagreements:
            lines.append(f"- {x}")
        lines.append("")

    lines.append(f"**Consensus:** {s.consensus}")
    lines.append("")
    lines.append(f"**Recommended action:** {s.recommended_action}")
    lines.append("")

    lines.append("---")
    lines.append("## Individual verdicts")
    for v in report.judges:
        lines.extend(_judge_md(v))

    lines.append("---")
    lines.append("## Run manifest")
    m = report.manifest
    lines.append(f"- **Fingerprint:** `{m.fingerprint()}`")
    lines.append(f"- **Schema version:** `{m.schema_version}`")
    lines.append(f"- **bojudges version:** `{m.bojudges_version}`")
    lines.append(f"- **Created:** {m.created_at.isoformat()}")
    lines.append(f"- **Temperature:** {m.temperature}")
    if m.seed is not None:
        lines.append(f"- **Seed:** {m.seed}")
    lines.append(f"- **Models:** `{m.models}`")
    lines.append(f"- **Total cost (USD):** {m.total_cost_usd:.4f}")
    lines.append(f"- **Wallclock (ms):** {m.total_duration_ms}")
    lines.append("")
    return "\n".join(lines)


def _judge_md(v: JudgeVerdict) -> list[str]:
    out = [
        "",
        f"### [Tier {v.tier}] {v.judge_name} — `{_VERDICT_ICON[v.verdict]}` "
        f"(score {v.score:.1f}, conf {v.confidence:.2f})",
        "",
        f"> {v.core_finding}",
        "",
    ]
    if v.error:
        out.append(f"⚠️  **Error:** {v.error}")
        out.append("")
    if not v.issues:
        out.append("No issues reported.")
        out.append("")
        return out

    for i in v.issues:
        mark = "✓" if i.verified else "✗ unverified"
        cwe = f" ({i.cwe})" if i.cwe else ""
        out.append(
            f"- **[{i.severity.value}]** {i.title}{cwe} — `{v.judge_id}:{i.id.split(':')[-1]}` {mark}"
        )
        out.append(f"  - File: `{i.file}` line {i.line}")
        out.append(f"  - Category: `{i.category}`")
        out.append(f"  - {i.description}")
        if i.fix_hint:
            out.append(f"  - Fix: {i.fix_hint}")
        if i.tool_citations:
            cites = ", ".join(f"`{c}`" for c in i.tool_citations)
            out.append(f"  - Evidence: {cites}")
    out.append("")
    return out
