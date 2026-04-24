# Benchmark

The Board of Judges project is committed to **publishing its own accuracy numbers**. This file is the canonical scoreboard per judge per dataset.

> _Current state: Phase 0. The `sqli_seed` dataset is live; real-model numbers arrive once the judge is calibrated._

## Why this is public

1. **Trust is the product.** If we can't measure our own quality, users shouldn't trust us to measure theirs.
2. **The moat.** Competitors don't publish theirs. When a CodeRabbit / Greptile / Qodo user asks "what's their accuracy?", the answer is "they don't say." We say.
3. **Regression gate.** CI runs `evals/` on every PR. A judge cannot merge a change that drops precision below its recorded floor.

## Datasets

| Name | Scope | Size | Purpose |
|------|-------|------|---------|
| `sqli_seed` | SQLi + command injection in Python | 10 snippets | Phase 0 gate |
| (planned) `sec_100` | Security, 5 categories, Python | 100 | Phase 2 security calibration |
| (planned) `backend_100` | Backend issues (API, DB, concurrency) | 100 | Phase 2 backend calibration |
| (planned) `frontend_100` | Frontend (XSS, accessibility, state) | 100 | Phase 2 frontend calibration |
| (planned) `adversarial_20` | Prompt-injection attempts inside submissions | 20 | Block-rate measurement |

## Per-judge scoreboard

| Judge | Tier | Dataset | Precision | Recall | F1 | ECE | Provider | Model | Date |
|-------|-----:|---------|----------:|-------:|---:|----:|----------|-------|------|
| `sec-appsec-injection` | 1 | `sqli_seed` | _pending_ | _pending_ | _pending_ | _pending_ | anthropic | claude-sonnet-4-6 | — |
| `sec-appsec-injection` | 1 | `sqli_seed` | 1.000 | 1.000 | 1.000 | 0.125 | **mock (plumbing)** | mock | 2026-04-24 |

_Mock row confirms the harness plumbing is correct. Real numbers replace it after the first real-model run._

### How to populate this file

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run python evals/runner.py --dataset sqli_seed --judge sec-appsec-injection
```

The runner writes `evals/reports/sqli_seed_sec-appsec-injection.json`. Copy the metrics into the table above with the date of the run and the model fingerprint from the report.

## Phase 0 gate

A judge cannot graduate from "seed" to "core calibrated" until it hits:

- Precision ≥ 0.70
- Recall ≥ 0.60
- ECE ≤ 0.15

If a judge is below these, it stays in `src/bojudges/judges/builtin/` but its manifest carries `calibration.temperature: null` — meaning its confidence is raw (uncalibrated), and downstream consumers treat it as advisory.

## Launch gate (Phase 3)

To move a judge into the advertised "core roster":

- Precision ≥ 0.75
- Recall ≥ 0.65
- ECE ≤ 0.10
- Line-verifier rejection rate < 15%
- Adversarial block rate ≥ 0.90 (if in the security/safety path)

## North-star targets

- Precision ≥ 0.85
- Recall ≥ 0.80
- ECE ≤ 0.05
