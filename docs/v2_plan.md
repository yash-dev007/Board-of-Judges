# Board of Judges — v2 Implementation Plan

Status: **Active**. Kickoff: 2026-04-24.

## The Thesis

Pure-LLM code review is a commodity race we will lose — incumbents (CodeRabbit, Greptile, Qodo) have distribution, we don't. The wedge is:

1. Every verdict is **grounded in a reproducible tool output** (semgrep hit, AST node, failing test, type error).
2. Every verdict's line citation is **verified** against the source file before the user sees it.
3. The whole system's accuracy is **benchmarked on a public eval set** that competitors won't publish because theirs is worse.
4. It runs in **every major coding CLI** — not just Claude Code.

The "board of judges" framing is UX flavor on top of a rubric-driven, tool-grounded pipeline.

---

## North Star

Product (one sentence): a CLI-and-GitHub review tool that runs a structured panel of specialist rubrics, grounds every finding in reproducible tool output, publishes its own accuracy scores, and is invokable from every major coding CLI.

ICP: OSS maintainers drowning in community PRs on Python / TypeScript repos who use a coding CLI (Claude Code, Gemini CLI, Codex, Cursor, Aider, etc.).

---

## Architecture

```
                      ┌───────────────────────────────────────────┐
                      │  Adapters (any coding CLI or bare shell)  │
                      │  claude-code · gemini-cli · codex ·       │
                      │  antigravity · aider · cursor · continue  │
                      │  · github-copilot-cli · github-action     │
                      └─────────────────┬─────────────────────────┘
                                        │ invokes
                                        ▼
                              ┌──────────────────┐
                              │  boj  (Python)   │
                              └────────┬─────────┘
                                       │
                     ┌─────────────────┼─────────────────┐
                     ▼                 ▼                 ▼
               ┌──────────┐    ┌───────────────┐   ┌──────────────┐
               │  Router  │───▶│ Panel Selector│──▶│  Dispatcher  │
               │ (Haiku)  │    │ (pure func)   │   │  (parallel)  │
               └──────────┘    └───────────────┘   └──────┬───────┘
                                                          │
                     ┌────────────────────────────────────┼───────────────┐
                     ▼                                    ▼               ▼
              ┌────────────┐                      ┌─────────────┐  ┌────────────┐
              │  Judge A   │                      │  Judge B    │  │  Judge C   │
              │  Tier 1    │                      │  Tier 1     │  │  Tier 2    │
              │  Sonnet    │                      │  Sonnet     │  │  Haiku     │
              │  + tools   │                      │  + tools    │  │  + tools   │
              └──────┬─────┘                      └──────┬──────┘  └──────┬─────┘
                     │                                   │                │
                     └───────────────────┬───────────────┴────────────────┘
                                         ▼
                               ┌──────────────────┐
                               │     Verifier     │
                               │  (line+symbol)   │
                               └────────┬─────────┘
                                        ▼
                               ┌──────────────────┐
                               │  Synthesizer     │
                               │  (Sonnet + think)│
                               └────────┬─────────┘
                                        ▼
                               ┌──────────────────┐
                               │   JSON + MD      │
                               └──────────────────┘
```

## Core Architecture Decisions

| # | Decision | Why |
|---|----------|-----|
| A1 | Standalone Python engine (`boj` CLI) | Consistent behavior across all host CLIs |
| A2 | Adapters are thin shims that invoke `boj judge <file>` and render the JSON | Quality stays uniform; host quirks don't bleed in |
| A3 | Provider-pluggable (Anthropic, Google, OpenAI, local) | Not locked to one vendor |
| A4 | Every judge outputs JSON via tool-use / function calling | Schema-validated, parseable, renderable |
| A5 | Judges call tools (semgrep, ast-grep, tsc, ruff, bandit) before reasoning | Grounds findings; hallucinations become detectable |
| A6 | Line+symbol verifier runs on every judge output | Cheap hallucination filter; rejects unverifiable citations |
| A7 | Per-judge confidence calibrated on eval set (Brier + ECE) | Confidence only means something if measured |
| A8 | Tiered models: Haiku for routing/style; Sonnet for reasoning-heavy | ~3× cost cut without quality loss |
| A9 | Reproducibility header on every report | Model/prompt/exemplar/seed hashes recorded |
| A10 | Disagreement is surfaced, not collapsed | A 6-PASS / 2-FAIL signal is valuable |
| A11 | Open benchmark (`evals/`), CI-gated | The moat. Trust is the product. |
| A12 | Start with ONE calibrated judge; expand by measurement | No judge ships without ≥0.75 precision |

---

## Target Repo Layout

```
board-of-judges/
├── src/bojudges/              Python package (core engine)
│   ├── core/                  router, panel, dispatcher, verifier, synthesizer
│   ├── providers/             anthropic, google, openai, mock
│   ├── tools/                 semgrep, ast, ruff, bandit, eslint, tsc
│   ├── judges/                base class, registry, builtin judges
│   ├── rendering/             terminal, markdown, github-comment
│   ├── schema/                pydantic models (verdict v1)
│   └── cli/                   typer app — `boj` entry point
├── adapters/                  thin integrations
│   ├── claude-code/           project .claude/ SKILL + agent override
│   ├── gemini-cli/            Gemini CLI skill file
│   ├── codex/                 AGENTS.md config
│   ├── antigravity/           config
│   ├── aider/                 custom command
│   ├── cursor/                .cursorrules
│   ├── continue/              config.json entry
│   ├── github-copilot-cli/    shell integration
│   └── github-action/         action.yaml
├── evals/
│   ├── datasets/              ground-truth YAML + code snippets
│   ├── runner.py              runs benchmark, emits precision/recall/ECE
│   └── reports/               generated
├── schemas/verdict.v1.json    frozen JSON schema (for external consumers)
├── tests/                     pytest, offline with mock provider
├── docs/                      architecture, adapters, plan
├── .claude/                   existing Claude Code integration (legacy + v2)
│   ├── agents/extended/       the 88 original judges (uncalibrated)
│   └── skills/                slash commands, updated to call boj
├── scripts/                   bootstrap scripts, adapter generators
├── pyproject.toml             uv-compatible, src layout
├── LICENSE                    MIT (previously claimed, now shipped)
├── README.md                  rewritten — evals-backed claims only
├── BENCHMARK.md               published numbers per judge
├── CONTRIBUTING.md            how to add judges, adapters, eval datasets
└── CLAUDE.md                  project context (updated for v2)
```

---

## Phase 0 — Spike (Days 1–3)

Goal: rebuild ONE judge end-to-end to the target spec. If the numbers aren't there on 10 snippets, architecture is wrong — find out now.

**Judge:** `sec-appsec-injection` (SQL injection + command injection subset of AppSec).

**Gate to proceed to Phase 1:**
- Precision ≥ 0.70
- Recall ≥ 0.60
- ECE ≤ 0.15

---

## Phase 1 — Foundation (Week 1)

Router + panel selector + JSON schema v1 frozen + real parallel dispatch + reproducibility header + opt-in telemetry.

**Exit:** `boj judge sample.py` runs 3 judges in parallel, all output valid JSON, every line citation verified, report has reproducibility header, cost printed.

---

## Phase 2 — Depth (Week 2)

Eval dataset to 100 snippets. 5 core judges calibrated: security, backend, frontend, architecture, performance.

**Exit:** Each judge ≥0.75 precision, ≥0.65 recall, ECE ≤0.10 on a public 100-snippet eval set.

---

## Phase 3 — Breadth + Launch (Week 3)

Cut 88 to 15–25 calibrated judges. Prompt-injection defenses. GitHub PR integration. Landing page. Launch.

**Exit:** Public repo with green CI, published eval numbers, PR integration demonstrated, landing page live, launch post drafted.

---

## Success Metrics

| Metric | Phase 0 gate | Launch gate | North star |
|--------|--------------|-------------|------------|
| Per-core-judge precision | ≥0.70 | ≥0.75 | ≥0.85 |
| Per-core-judge recall | ≥0.60 | ≥0.65 | ≥0.80 |
| Expected Calibration Error (ECE) | ≤0.15 | ≤0.10 | ≤0.05 |
| Line-number verifier rejection rate | <30% | <15% | <5% |
| Adversarial block rate | n/a | ≥0.90 | ≥0.97 |
| Median review cost (500 LoC, 10 judges) | n/a | ≤$0.12 | ≤$0.08 |
| Median review wall-clock | n/a | ≤90s | ≤45s |
| Prompt-cache hit rate on 2nd run in session | n/a | ≥0.60 | ≥0.80 |

---

## Explicitly Not Doing (until v3+)

- Per-line inline PR comments (CodeRabbit's turf; commoditized)
- Auto-fix / auto-apply (trust-destroying failure mode)
- Multi-repo / monorepo-at-scale (enterprise, different product)
- Web UI (terminal + GitHub comment proves PMF)
- Custom judges from end-users (Pro feature in v3)
- Languages beyond Python + TypeScript at launch (Go/Rust in v2)

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| Eval dataset is too small/biased | Mix sources, track provenance, grow weekly, accept bugs publicly |
| Tool grounding undermines "AI review" story | Reposition: "AI-orchestrated expert review, not AI-generated vibes" |
| Anthropic/Google/OpenAI ship model updates mid-build | Pin model IDs; re-run evals on upgrade; publish deltas |
| Prompt cache design wrong → cost spike | Cache per-judge prefix; verify hit rate from day 1 |
| Phase 0 fails gate | Redesign on cheap information; do not advance |
| Users submit enormous files | Size guard: >1500 LoC → require `--chunk` flag |
| Schema changes break downstream consumers | Version the JSON schema; additive-only in minor versions |
| Hallucinations below line-number granularity | Verifier also checks cited tokens exist in file |
