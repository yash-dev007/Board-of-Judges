---
name: judge
description: >
  Board of Judges v2 — tool-grounded, eval-backed panel code review.
  Shells out to the `boj` Python CLI. Usage: /judge <file> [--panel X]
  [--solo X] [--all]
---

# Board of Judges — Gemini CLI adapter

When the user invokes `/judge <file>`:

1. Verify `boj` is on PATH with `boj version`. If missing, instruct them to
   `uv sync --dev` or `pip install -e .` from the repo root.

2. Run:
   ```
   boj judge <file> [--panel <tags>] [--solo <judge-id>] [--all] \
     --markdown judgements/gemini-<timestamp>-<slug>.md \
     --output   judgements/gemini-<timestamp>-<slug>.json
   ```

3. Read the markdown file and display it verbatim. Do not editorialize.

4. If the exit code is non-zero and the verdict was `FAIL`, summarize the
   critical issues in one line at the top.

5. If the user passes `--post-to-pr`, check for an active PR context via
   `gh pr view --json number` and post the markdown as a comment.

The actual review logic (judge selection, tool grounding, verification,
synthesis) is owned by `boj`. This skill is a thin launcher.
