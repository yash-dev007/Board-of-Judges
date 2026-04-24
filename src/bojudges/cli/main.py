from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from bojudges import __schema_version__, __version__
from bojudges.core.dispatcher import DispatchConfig, Dispatcher
from bojudges.core.panel import PanelSelector
from bojudges.core.router import Router
from bojudges.core.synthesizer import RuleBasedSynthesizer
from bojudges.core.verifier import LineVerifier
from bojudges.judges import JudgeRegistry, load_builtin_judges
from bojudges.judges.base import JudgeContext
from bojudges.rendering import print_report, report_to_markdown
from bojudges.schema import BoardReport, RunManifest, SubmissionRef

app = typer.Typer(
    add_completion=False,
    help="Board of Judges — tool-grounded panel code review.",
)
console = Console()


@app.command("version")
def cmd_version() -> None:
    """Print bojudges version and schema version."""
    console.print(f"bojudges {__version__}  (schema v{__schema_version__})")


@app.command("judge")
def cmd_judge(
    target: Path = typer.Argument(..., exists=True, readable=True, help="File to review."),
    panel: str | None = typer.Option(None, "--panel", help="Comma-separated tag filter."),
    solo: str | None = typer.Option(None, "--solo", help="Run exactly this judge ID."),
    allow_all: bool = typer.Option(False, "--all", help="Remove the 10-judge cap."),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write JSON report to this path."
    ),
    markdown: Path | None = typer.Option(
        None, "--markdown", "-m", help="Write Markdown report to this path."
    ),
    format: str = typer.Option(  # noqa: A002 — user-facing flag name
        "terminal",
        "--format",
        "-f",
        help="Output format: terminal | json | markdown.",
    ),
    judges_dir: Path | None = typer.Option(
        None, "--judges-dir", help="Extra directory to load judges from (manifest.yaml files)."
    ),
    seed: int | None = typer.Option(None, "--seed", help="Deterministic seed."),
    temperature: float = typer.Option(0.3, "--temperature", help="LLM temperature."),
    max_judges: int = typer.Option(10, "--max-judges", help="Cap on panel size."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Route + select panel only; do NOT call any LLM."
    ),
) -> None:
    """Run a panel review on TARGET."""
    target_path = target.resolve()
    content = target_path.read_text(encoding="utf-8", errors="replace")
    sha = hashlib.sha256(content.encode()).hexdigest()

    router = Router()
    route = router.route(str(target_path), content)

    registry = load_builtin_judges()
    if judges_dir:
        extra = JudgeRegistry.from_dir(judges_dir)
        for j in extra.judges:
            registry.add(j)

    if len(registry) == 0:
        console.print("[red]No judges loaded. Check src/bojudges/judges/builtin/[/red]")
        raise typer.Exit(code=2)

    panel_filter = [p.strip() for p in panel.split(",")] if panel else None
    selector = PanelSelector(max_judges=max_judges)
    items = selector.select(
        list(registry),
        route,
        panel_filter=panel_filter,
        solo=solo,
        allow_all=allow_all,
    )

    if not items:
        console.print("[yellow]No judges matched the panel filter.[/yellow]")
        raise typer.Exit(code=1)

    console.print(f"[blue]Panel:[/] {len(items)} judge(s) selected for `{target_path.name}`")
    for it in items:
        console.print(f"  [Tier {it.judge.tier}] {it.judge.name}  (score={it.score:.2f})")

    if dry_run:
        raise typer.Exit(code=0)

    ctx = JudgeContext(
        submission_path=str(target_path),
        submission_content=content,
        language=route.language,
    )

    config = DispatchConfig(seed=seed, temperature=temperature)
    dispatcher = Dispatcher(verifier=LineVerifier(), config=config)

    t0 = time.perf_counter()
    verdicts = dispatcher.dispatch(items, ctx)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    synth = RuleBasedSynthesizer().synthesize(verdicts)

    models_used = {v.judge_id: v.model_id for v in verdicts}
    manifest = RunManifest(
        bojudges_version=__version__,
        models=models_used,
        temperature=temperature,
        seed=seed,
        prompt_hashes={v.judge_id: v.prompt_hash for v in verdicts},
        exemplars_hashes={v.judge_id: v.exemplars_hash for v in verdicts},
        total_cost_usd=sum(v.cost_usd for v in verdicts),
        total_duration_ms=elapsed_ms,
    )
    report = BoardReport(
        submission=SubmissionRef(
            path=str(target_path),
            sha256=sha,
            size_bytes=len(content.encode()),
            language=route.language,
            loc=route.loc,
        ),
        judges=verdicts,
        synthesis=synth,
        manifest=manifest,
    )

    if output:
        output.write_text(report.pretty_json(), encoding="utf-8")
        console.print(f"[dim]JSON written to {output}[/dim]")
    if markdown:
        markdown.write_text(report_to_markdown(report), encoding="utf-8")
        console.print(f"[dim]Markdown written to {markdown}[/dim]")

    if not output and not markdown:
        judgements_dir = Path("judgements")
        judgements_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        slug = target_path.stem.replace(" ", "-")
        auto = judgements_dir / f"{stamp}-{slug}.md"
        auto.write_text(report_to_markdown(report), encoding="utf-8")
        console.print(f"[dim]Report saved to {auto}[/dim]")

    if format == "json":
        sys.stdout.write(report.pretty_json() + "\n")
    elif format == "markdown":
        sys.stdout.write(report_to_markdown(report) + "\n")
    else:
        print_report(report)

    if synth.board_verdict.value == "FAIL":
        raise typer.Exit(code=1)


@app.command("list-judges")
def cmd_list_judges(
    judges_dir: Path | None = typer.Option(None, "--judges-dir"),
) -> None:
    """List all available judges."""
    registry = load_builtin_judges()
    if judges_dir:
        extra = JudgeRegistry.from_dir(judges_dir)
        for j in extra.judges:
            registry.add(j)
    t = Table(title=f"Available judges ({len(registry)})")
    t.add_column("ID")
    t.add_column("Name")
    t.add_column("Tier", justify="right")
    t.add_column("Tags")
    t.add_column("Model")
    t.add_column("Calibrated?")
    for j in registry:
        t.add_row(
            j.id,
            j.name,
            str(j.tier),
            ",".join(j.tags),
            j.model_id,
            "yes" if j.calibration_temperature is not None else "no",
        )
    console.print(t)


@app.command("route")
def cmd_route(target: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    """Show how the router would classify a file (no LLM call)."""
    content = target.read_text(encoding="utf-8", errors="replace")
    route = Router().route(str(target), content)
    payload = {
        "path": str(target),
        "language": route.language,
        "loc": route.loc,
        "domain_tags": route.domain_tags,
        "risk_tags": route.risk_tags,
        "sensitivity": route.sensitivity,
    }
    console.print(json.dumps(payload, indent=2))


@app.command("schema")
def cmd_schema() -> None:
    """Print the verdict JSON schema."""
    from bojudges.schema import BoardReport
    console.print(json.dumps(BoardReport.model_json_schema(), indent=2))


if __name__ == "__main__":
    app()
