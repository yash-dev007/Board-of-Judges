# Claude Code adapter

Ships as a project-local skill. Clone the repo and open it in Claude Code — the skill activates automatically.

## Install (already done if you cloned this repo)

The skill lives at `.claude/skills/judge-v2/SKILL.md`. It replaces the v1 in-context roleplay loop with a shell-out to `boj`.

## Prerequisites

1. Install `boj`:
   ```bash
   cd board-of-judges
   uv sync --dev        # or: pip install -e .
   ```
2. Export an API key (any one of):
   ```bash
   export ANTHROPIC_API_KEY=...
   export GOOGLE_API_KEY=...
   export OPENAI_API_KEY=...
   ```

## Usage

```
/judge path/to/file.py
/judge path/to/file.py --panel security
/judge path/to/file.py --solo sec-appsec-injection
/judge path/to/file.py --all
```

## What the skill does

1. Parses flags.
2. Runs `boj judge <file> --format markdown --output judgements/<stamp>.json`.
3. Displays the rendered panel verdicts.
4. (If `--post-to-pr`) Runs `gh pr comment` with the markdown report.

## Legacy agents

The 88 original role-play judges are preserved at `.claude/agents/extended/`. They are **uncalibrated** and kept for backwards compatibility. New work should use `boj` and the core builtin judges.
