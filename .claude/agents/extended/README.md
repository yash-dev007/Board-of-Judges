# Legacy / Extended judges

These are the **88 original role-play judges** from v1 of the Board of Judges.

> ⚠️  **They are UNCALIBRATED.** They have never been benchmarked on a real eval set. Use at your own risk — treat their verdicts as advisory, not authoritative.

## Why they're preserved here

1. Backwards compatibility with the legacy `/judge` skill.
2. Source material for future calibrated judges — each one of these can be ported to `src/bojudges/judges/builtin/<id>/` once eval data exists for its domain.

## How to use them

- Via the legacy skill: `/judge <file>` (the v1 Claude-Code roleplay loop).
- Via direct invocation: `@judge-<name>` in Claude Code.
- They do **NOT** load into the `boj` CLI. They are project-local Claude Code agents only.

## Promotion path

To promote a legacy agent to a core calibrated judge:

1. Pick an agent in this directory.
2. Identify the scope (e.g. `judge-sec-cryptography-encryption-specialist.md` → "cryptography misuse" domain).
3. Build an eval dataset of at least 10 snippets (5 positive, 5 negative) in `evals/datasets/<scope>_seed/`.
4. Create `src/bojudges/judges/builtin/<judge-id>/` with:
   - `manifest.yaml` — with tags, risk_tags, model, tools, and `calibration: {}` (empty = uncalibrated)
   - `persona.md` — adapt the legacy agent's persona; add "what you look for that others miss" + "what you do NOT flag"
   - `exemplars.jsonl` — 2–3 worked examples
5. Run `evals/runner.py --dataset <scope>_seed --judge <id>`. Record numbers in `BENCHMARK.md`.
6. If it hits the Phase 0 gate (P ≥ 0.70, R ≥ 0.60, ECE ≤ 0.15), it's a core judge.

No shortcut. No "promote on vibes."

## The index

`scripts/bootstrap_claude_judges.py` remains the source of truth for regenerating this directory. Edit the Python list, then:

```bash
uv run python scripts/bootstrap_claude_judges.py --output .claude/agents/extended
```

(Note: the script still writes to `.claude/agents/` by default. Pass `--output .claude/agents/extended` or update the script if you want extended-by-default.)
