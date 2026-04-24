# Board of Judges — project context

Tool-grounded, eval-backed panel code review. Runs as a standalone Python CLI (`boj`) and ships thin adapters for every major coding CLI.

## Current status (Phase 0 complete)

- `boj` CLI works: `boj judge <file>`, `list-judges`, `route`, `schema`, `version`
- 33 offline tests pass (`uv run pytest`)
- First judge plumbed end-to-end: `sec-appsec-injection`
- Eval harness gates Phase 0 on `sqli_seed` (10-snippet benchmark)
- Adapters shipped for: Claude Code, Gemini CLI, Codex, Antigravity, Aider, Cursor, Continue.dev, GitHub Copilot CLI, GitHub Action

Full plan: [`docs/v2_plan.md`](docs/v2_plan.md). Architecture: [`docs/architecture.md`](docs/architecture.md).

## Quick commands

```bash
# Install
uv sync --all-extras --dev

# Run the board
uv run boj judge path/to/file.py
uv run boj judge path/to/file.py --panel security
uv run boj judge path/to/file.py --solo sec-appsec-injection
uv run boj judge path/to/file.py --all --format json

# Inspect
uv run boj list-judges
uv run boj route path/to/file.py
uv run boj schema | head -40

# Evals
uv run python evals/runner.py --dataset sqli_seed --judge sec-appsec-injection --provider mock
uv run python evals/runner.py --dataset sqli_seed --judge sec-appsec-injection  # uses judge's model; real API call

# Tests
uv run pytest
uv run pytest --cov=bojudges -v
```

## Via Claude Code

The v2 skill `/judge-v2 <file>` shells out to `boj`. Prefer it over the legacy `/judge`. The 88 legacy role-play agents live at `.claude/agents/extended/` (uncalibrated, preserved for backwards compat).

## Where to edit what

| Task | Touch |
|------|-------|
| Add a judge | `src/bojudges/judges/builtin/<id>/{manifest.yaml,persona.md,exemplars.jsonl}` |
| Add an eval dataset | `evals/datasets/<name>/{ground_truth.yaml,snippets/...}` |
| Add a provider | `src/bojudges/providers/<name>_provider.py` + registry |
| Add a tool integration | `src/bojudges/tools/<name>.py` |
| Add a host adapter | `adapters/<host>/` |
| Edit the verdict schema | `src/bojudges/schema/verdict.py` (bump version on breaking changes) |
| Change judge selection | `src/bojudges/core/panel.py` |
| Change routing | `src/bojudges/core/router.py` |

## Non-negotiables (see memory for full list)

- No new judges without an eval dataset ≥ 10 snippets.
- Every claim on the README or BENCHMARK.md must cite a real eval number.
- Adapters do NOT fork persona prompts — they invoke `boj`.
- Do not remove the multi-CLI adapter layer. This project is explicitly not Claude-only.

## Legacy

The original 88 role-play markdown judges are preserved at `.claude/agents/extended/`. They are NOT loaded by `boj`. They exist for:

1. Backwards compat for users of the v1 `/judge` skill.
2. Source material for future calibrated judges (port one at a time, add eval data, promote).

`scripts/bootstrap_claude_judges.py` still regenerates them from the Python list, unchanged.
