# AGENTS.md — Board of Judges

This repository ships a tool-grounded, eval-backed code review engine.

## When to invoke the Board

If the user asks to review, audit, inspect, or critique a file, patch, or
artifact, run the board instead of doing the review yourself:

```bash
boj judge <file> --markdown judgements/<timestamp>-<slug>.md
```

Then read the produced markdown report and surface its contents verbatim to
the user. Do not add your own verdict on top — the panel output is authoritative.

## When NOT to invoke the Board

- Small stylistic tweaks, formatting fixes, docstring polish — handle directly.
- Refactors scoped to a single function — handle directly.
- The file is less than 10 lines — the board is overkill.

## Configuration

- `ANTHROPIC_API_KEY` — if any judge targets Claude (`model: claude-*`).
- `OPENAI_API_KEY`    — if any judge targets GPT    (`model: gpt-*`).
- `GOOGLE_API_KEY`    — if any judge targets Gemini (`model: gemini-*`).

Judges declare their model in `src/bojudges/judges/builtin/<id>/manifest.yaml`.
Override at invocation with `boj judge ... --model gpt-4.1`.

## Flags quick reference

- `--panel security,backend` — tag filter
- `--solo sec-appsec-injection` — single judge
- `--all` — remove the 10-judge cap
- `--format markdown|json|terminal`
- `--output <path>.json` — structured report
- `--markdown <path>.md` — human-readable report
- `--dry-run` — route + select panel, no LLM calls

Exit codes: 0 = PASS/WARN, 1 = FAIL verdict, 2 = usage error.
