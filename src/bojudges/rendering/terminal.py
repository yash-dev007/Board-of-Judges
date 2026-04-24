from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bojudges.schema import BoardReport, JudgeVerdict, Severity, Verdict

_VERDICT_STYLE = {
    Verdict.PASS: "bold green",
    Verdict.WARN: "bold yellow",
    Verdict.FAIL: "bold red",
    Verdict.SKIP: "dim",
}

_SEVERITY_STYLE = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan",
    Severity.INFO: "dim",
}


def print_report(report: BoardReport, console: Console | None = None) -> None:
    console = console or Console()

    header = Text.assemble(
        ("Board of Judges ", "bold"),
        (f"— {report.submission.path}", ""),
    )
    console.print(Panel(header, border_style="blue"))

    table = Table(title="Judges", show_lines=False, header_style="bold")
    table.add_column("Tier")
    table.add_column("Judge")
    table.add_column("Verdict")
    table.add_column("Score", justify="right")
    table.add_column("Conf", justify="right")
    table.add_column("Issues", justify="right")
    table.add_column("ms", justify="right")
    for v in report.judges:
        table.add_row(
            str(v.tier),
            v.judge_name,
            Text(v.verdict.value, style=_VERDICT_STYLE[v.verdict]),
            f"{v.score:.1f}",
            f"{v.confidence:.2f}",
            str(sum(1 for i in v.issues if i.verified)),
            str(v.duration_ms),
        )
    console.print(table)

    for v in report.judges:
        _print_judge(console, v)

    _print_synthesis(console, report)
    _print_footer(console, report)


def _print_judge(console: Console, v: JudgeVerdict) -> None:
    title = Text.assemble(
        (f"[Tier {v.tier}] ", "dim"),
        (v.judge_name, "bold"),
        ("  ", ""),
        (v.verdict.value, _VERDICT_STYLE[v.verdict]),
        (f"  score={v.score:.1f}  conf={v.confidence:.2f}", "dim"),
    )
    body_lines: list[str] = []
    if v.core_finding:
        body_lines.append(v.core_finding)
    if not v.issues:
        body_lines.append("\nNo issues reported.")
    else:
        body_lines.append("")
        for i in v.issues:
            status = "[green]✓[/green]" if i.verified else "[red]✗ unverified[/red]"
            body_lines.append(
                f"[{_SEVERITY_STYLE[i.severity]}]{i.severity.value:<8}[/] "
                f"{i.category} @ line {i.line}  {status}"
            )
            body_lines.append(f"  {i.title}")
            if i.fix_hint:
                body_lines.append(f"  [dim]fix:[/] {i.fix_hint}")
    console.print(Panel("\n".join(body_lines), title=title, border_style="blue"))


def _print_synthesis(console: Console, report: BoardReport) -> None:
    s = report.synthesis
    vs = _VERDICT_STYLE[s.board_verdict]
    title = Text.assemble(
        ("BOARD VERDICT: ", "bold"),
        (s.board_verdict.value, vs),
        (f"  score={s.board_score:.1f}", "dim"),
    )
    parts: list[str] = []
    if s.critical_issues:
        parts.append("[bold red]Critical:[/]")
        parts.extend(f"  • {x}" for x in s.critical_issues)
    if s.warnings:
        parts.append("[bold yellow]Warnings:[/]")
        parts.extend(f"  • {x}" for x in s.warnings)
    if s.disagreements:
        parts.append("[bold magenta]Disagreements (surfaced, not collapsed):[/]")
        parts.extend(f"  • {x}" for x in s.disagreements)
    parts.append(f"\n[bold]Consensus:[/] {s.consensus}")
    parts.append(f"[bold]Recommended action:[/] {s.recommended_action}")
    console.print(Panel("\n".join(parts), title=title, border_style="yellow"))


def _print_footer(console: Console, report: BoardReport) -> None:
    m = report.manifest
    console.print(
        f"[dim]fingerprint={m.fingerprint()}  cost=${m.total_cost_usd:.4f}  "
        f"wallclock={m.total_duration_ms}ms  models={m.models}[/dim]"
    )
