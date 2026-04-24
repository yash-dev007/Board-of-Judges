# Board of Judges

**Tool-grounded, eval-backed panel code review. Runs in every major coding CLI.**

`boj` classifies a submission, picks the right specialist judges, runs each in parallel against static-analysis tools + a language model, verifies every cited line, and emits a structured verdict.

> **Status:** v0.2 alpha — Phase 0 complete. Pipeline end-to-end on mock provider. First calibrated judge: `sec-appsec-injection`.

---

## Why this exists

1. Most AI code-review tools hallucinate. We ground every finding in a reproducible tool output and verify line citations.
2. Most AI code-review tools publish zero accuracy numbers. We publish ours — per judge, per dataset, in [`BENCHMARK.md`](BENCHMARK.md).
3. Most AI code-review tools lock you to one host. We ship [adapters for every major coding CLI](adapters/).

---

## Quick start

```bash
# Install
git clone https://github.com/yash-dev007/board-of-judges
cd board-of-judges
uv sync --all-extras --dev   # or: pip install -e .

# Set one API key (any provider works; judges declare which model they want)
export ANTHROPIC_API_KEY=sk-ant-...
# or GOOGLE_API_KEY, or OPENAI_API_KEY

# Run
uv run boj judge path/to/your/file.py
```

### Offline smoke test (no API key needed)

```bash
uv run pytest                                 # runs 33 tests, ~1s
uv run boj list-judges                        # shows the calibrated roster
uv run boj route path/to/file.py              # see how the router would classify
uv run python evals/runner.py \               # validate the full pipeline
    --dataset sqli_seed \
    --judge sec-appsec-injection \
    --provider mock
```

---

## How it works

```
  Adapter (Claude Code / Gemini CLI / Codex / Cursor / Aider / …)
                        │
                        ▼
                ┌──────────────┐
                │   boj CLI    │   Python, MIT-licensed, pip-installable
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌────────┐    ┌──────────┐   ┌──────────┐
   │ Router │───▶│  Panel   │──▶│Dispatcher│
   └────────┘    └──────────┘   └─────┬────┘
                                      │ parallel, one LLM call per judge
                  ┌───────────────────┼───────────────────┐
                  ▼                   ▼                   ▼
             ┌────────┐         ┌──────────┐         ┌──────────┐
             │Judge A │         │ Judge B  │         │ Judge C  │
             │ tools+ │         │  tools+  │         │  tools+  │
             │  LLM   │         │   LLM    │         │   LLM    │
             └───┬────┘         └─────┬────┘         └─────┬────┘
                 └────────┬───────────┴────────┬───────────┘
                          ▼                    ▼
                  Verifier (line+symbol)   Synthesizer (rule-based)
                          │                    │
                          └────────┬───────────┘
                                   ▼
                            JSON + Markdown report
```

Full design: [`docs/architecture.md`](docs/architecture.md).

---

## Runs in every major coding CLI

| Host | Path | Activation |
|------|------|------------|
| Plain terminal | everywhere | `boj judge <file>` |
| Claude Code | [`adapters/claude-code/`](adapters/claude-code/) | `/judge-v2 <file>` |
| Gemini CLI | [`adapters/gemini-cli/`](adapters/gemini-cli/) | `/judge <file>` |
| OpenAI Codex | [`adapters/codex/`](adapters/codex/) | via `AGENTS.md` |
| Google Antigravity | [`adapters/antigravity/`](adapters/antigravity/) | config entry |
| Aider | [`adapters/aider/`](adapters/aider/) | `!boj judge <file>` |
| Cursor | [`adapters/cursor/`](adapters/cursor/) | `.cursorrules` |
| Continue.dev | [`adapters/continue/`](adapters/continue/) | `/judge` slash command |
| GitHub Copilot CLI | [`adapters/github-copilot-cli/`](adapters/github-copilot-cli/) | shell alias |
| GitHub Action | [`adapters/github-action/`](adapters/github-action/) | in your workflow |

Adding a host is typically 3 files. See [`docs/adapters.md`](docs/adapters.md).

---

## Providers

Any judge can target any provider. The `model` field in a judge's `manifest.yaml` drives the choice:

| Provider | Models | Env var |
|----------|--------|---------|
| Anthropic | `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5` | `ANTHROPIC_API_KEY` |
| Google | `gemini-2.5-pro`, `gemini-2.5-flash` | `GOOGLE_API_KEY` |
| OpenAI | `gpt-4.1`, `gpt-4o`, `o3-mini` | `OPENAI_API_KEY` |

---

## What's in v0.2 (Phase 0)

- ✅ `boj` CLI: `judge`, `list-judges`, `route`, `schema`, `version`
- ✅ Provider abstraction: Anthropic (ready), Google + OpenAI (plug-in stubs; require optional deps)
- ✅ Tool grounding via `semgrep` (graceful fallback when not installed)
- ✅ Line + symbol verifier — every issue's citation is checked before the user sees it
- ✅ Rule-based synthesizer with disagreement surfacing
- ✅ JSON schema v1 (Pydantic) for every report
- ✅ RunManifest with fingerprint (model + prompt + exemplar hashes) — fully reproducible
- ✅ Eval harness with `sqli_seed` (10-snippet SQLi + command-injection benchmark)
- ✅ 33 offline tests
- ✅ Adapters for 9 hosts
- ✅ First calibrated-in-progress judge: `sec-appsec-injection`
- ✅ 88 legacy role-play judges preserved at `.claude/agents/extended/` (uncalibrated)

What's not in v0.2 yet:
- Additional judges beyond the first (calibrated ones arrive in Phase 2)
- Real-model BENCHMARK numbers (requires API key to generate)
- Prompt-injection adversarial eval set
- GitHub PR auto-comment polish
- Landing page

See [`docs/v2_plan.md`](docs/v2_plan.md) for the full roadmap.

---

## Verdict structure

Every report is valid JSON. A minimal verdict:

```json
{
  "submission": { "path": "login.py", "sha256": "...", "language": "python" },
  "judges": [
    {
      "judge_id": "sec-appsec-injection",
      "judge_name": "Application Security — Injection Specialist",
      "tier": 1,
      "verdict": "FAIL",
      "score": 2.0,
      "confidence": 0.92,
      "core_finding": "String concatenation into cursor.execute() at line 4.",
      "issues": [
        {
          "id": "sec-appsec-injection:0",
          "severity": "CRITICAL",
          "title": "SQL injection via string concatenation",
          "file": "login.py",
          "line": 4,
          "cwe": "CWE-89",
          "category": "sql-injection",
          "fix_hint": "Use parameterized queries: cur.execute(sql, (name,))",
          "verified": true,
          "tool_source": "hybrid",
          "tool_citations": ["semgrep:python.django.security.sql-injection@login.py:4"]
        }
      ]
    }
  ],
  "synthesis": {
    "board_verdict": "FAIL",
    "board_score": 2.0,
    "critical_issues": [...],
    "consensus": "...",
    "disagreements": [...],
    "recommended_action": "Fix 1 critical issue(s) before merging."
  },
  "manifest": {
    "bojudges_version": "0.2.0a0",
    "schema_version": "1.0",
    "models": { "sec-appsec-injection": "claude-sonnet-4-6" },
    "temperature": 0.3,
    "seed": 42,
    "prompt_hashes": { "sec-appsec-injection": "abc123..." },
    "total_cost_usd": 0.04,
    "total_duration_ms": 2100
  }
}
```

---

## Benchmarks

Every quality claim is backed by a number in [`BENCHMARK.md`](BENCHMARK.md). A judge is NOT promoted to the core roster until it hits the Phase 0 gate (precision ≥ 0.70, recall ≥ 0.60, ECE ≤ 0.15) on a public eval set.

---

## Project layout

```
board-of-judges/
├── src/bojudges/              Core engine (Python)
│   ├── schema/                Pydantic models
│   ├── providers/             Anthropic, Google, OpenAI, Mock
│   ├── tools/                 semgrep (more arriving)
│   ├── core/                  Router, Panel, Dispatcher, Verifier, Synthesizer
│   ├── judges/                Base class + registry + builtin/
│   ├── rendering/             Terminal + Markdown
│   └── cli/                   typer app — `boj`
├── adapters/                  Thin shims for each coding CLI
├── evals/                     Benchmark datasets + runner
├── tests/                     Offline pytest suite
├── docs/                      Plan, architecture, adapter guide
├── .claude/
│   ├── skills/                v2 skill — shells out to boj
│   └── agents/extended/       88 legacy role-play judges (preserved)
├── pyproject.toml
├── LICENSE                    MIT
├── README.md
├── BENCHMARK.md               Published accuracy numbers
└── CONTRIBUTING.md
```

---

## License

MIT. See [`LICENSE`](LICENSE).

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Every quality-affecting change must ship with an eval run.
