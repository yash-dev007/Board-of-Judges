---
name: judge-v2
description: >
  Board of Judges v2 — tool-grounded, eval-backed panel code review.
  Invokes the `boj` CLI; returns a structured verdict report.
  Usage: /judge-v2 <target> [--panel X] [--solo X] [--all] [--post-to-pr]
---

# Board of Judges — v2 Coordinator

You are the **v2 coordinator**. You do NOT roleplay judges. Each judge is run by
the `boj` Python CLI, which dispatches real parallel LLM calls, grounds every
finding in static-analysis tool output, verifies line-number citations, and
emits structured JSON.

## Step 1 — Parse invocation

Extract:
- `target`: file path (required — ask if missing).
- `--panel <tags>`: comma-separated tag filter.
- `--solo <judge-id>`: run a single judge.
- `--all`: no 10-judge cap.
- `--post-to-pr`: after review, post to current branch's PR via `gh`.

## Step 2 — Confirm `boj` is installed

Run `boj version`. If it fails:

```
boj not installed. Install from the repo root:
  uv sync --dev        (preferred)
  pip install -e .     (alternative)
Then set ANTHROPIC_API_KEY / GOOGLE_API_KEY / OPENAI_API_KEY.
```

Do not proceed until `boj` is available.

## Step 3 — Run the review

```bash
boj judge <target> \
  [--panel <tags>] \
  [--solo <id>] \
  [--all] \
  --output judgements/<timestamp>-<slug>.json \
  --markdown judgements/<timestamp>-<slug>.md
```

Capture exit code. `0` = PASS/WARN, `1` = FAIL, `2` = usage error.

## Step 4 — Render the report

The markdown report at `judgements/<timestamp>-<slug>.md` contains:
- Verdict table with scores, confidence, issue counts
- Individual judge verdicts with issues, fix hints, tool citations
- Run manifest (fingerprint, models, cost, duration)
- Disagreements (surfaced, not collapsed)

Read the markdown and display it to the user. Do not add your own commentary
on top of the judges' verdicts.

## Step 5 — Post to PR (if requested)

Only if `--post-to-pr` was passed and `gh pr view` succeeds:

```bash
gh pr comment $(gh pr view --json number -q .number) \
  --body-file judgements/<timestamp>-<slug>.md
```

Report the PR URL.

## Rules

- Never fabricate judge verdicts. The `boj` output is authoritative.
- If `boj judge` errors, show stderr and stop — do not improvise a review.
- The 88 legacy agents under `.claude/agents/extended/` are NOT part of v2.
  Use them only if the user explicitly invokes `@judge-...` directly.
