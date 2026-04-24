# Architecture

## Core principle

`boj` is a **review engine**, not a chat persona. It runs its own parallel judges, calls LLM providers directly, grounds every finding in static-analysis tool output, verifies line citations, and emits structured JSON. Coding CLIs are thin adapters that invoke it.

```
  Adapter (Claude Code / Gemini CLI / Codex / Cursor / Aider / etc.)
                        │
                        │  shells out
                        ▼
                ┌──────────────┐
                │   boj CLI    │
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌────────┐    ┌──────────┐   ┌──────────┐
   │ Router │───▶│  Panel   │──▶│Dispatcher│
   │        │    │ Selector │   │(parallel)│
   └────────┘    └──────────┘   └─────┬────┘
                                      │
                  ┌───────────────────┼───────────────────┐
                  ▼                   ▼                   ▼
             ┌────────┐         ┌──────────┐         ┌──────────┐
             │Judge A │         │ Judge B  │         │ Judge C  │
             │ tools+ │         │  tools+  │         │  tools+  │
             │  LLM   │         │   LLM    │         │   LLM    │
             └───┬────┘         └─────┬────┘         └─────┬────┘
                 │                    │                    │
                 └────────────────────┼────────────────────┘
                                      ▼
                              ┌──────────────┐
                              │  Verifier    │
                              │(line+symbol) │
                              └──────┬───────┘
                                     ▼
                              ┌──────────────┐
                              │ Synthesizer  │
                              │ (rule-based) │
                              └──────┬───────┘
                                     ▼
                              ┌──────────────┐
                              │  BoardReport │
                              │  JSON + MD   │
                              └──────────────┘
```

## Modules

### `bojudges.schema`
Pydantic models for `Issue`, `JudgeVerdict`, `Synthesis`, `RunManifest`, `BoardReport`. Every report is fully round-trippable via `model_dump_json()` / `model_validate_json()`. Schema version lives in `bojudges.__schema_version__`.

### `bojudges.providers`
- `base.Provider` — abstract interface: `generate(messages, model, tools, …) -> LLMResponse`, `cost_usd(response)`, `supports_prompt_cache()`.
- `anthropic_provider.AnthropicProvider` — uses the `anthropic` SDK. Tool-use via `tools=` + `tool_choice={"type":"tool","name":...}`. Ephemeral prompt caching on system + long-stable user blocks.
- `google_provider.GoogleProvider` — uses `google-genai`. Function declarations + tool config (`ANY` / named).
- `openai_provider.OpenAIProvider` — uses `openai`. Function tools + `tool_choice={type:"function", function:{name}}`.
- `mock.MockProvider` — offline, scripted. Used in all tests and for eval-harness dry runs.
- `registry.get_provider(name)` — factory; `resolve_model_provider(model_id)` — heuristic mapping of model IDs to providers (`claude-*` → anthropic, `gemini-*` → google, `gpt-*` / `o1-*` / `o3-*` → openai).

### `bojudges.tools`
Static-analysis integrations. Each `Tool` implements `available()` and `run(file_path, content) -> list[Finding]`. Gracefully degrades when the tool is missing.

Currently shipped:
- `SemgrepTool` — runs `semgrep scan --json` with the configured rulesets (`p/security-audit`, `p/sql-injection`, etc.).

Planned (stubs arrive as judges need them): `BanditTool`, `RuffTool`, `ESLintTool`, `TscTool`, `ASTTool`.

### `bojudges.core`
- `Router` — deterministic extension + substring classifier. Emits `{language, domain_tags, risk_tags, loc, sensitivity}`. Phase 1+ will add an optional Haiku-based content classifier for ambiguous files.
- `PanelSelector` — scores each judge on `tag_overlap + 2*risk_overlap + tier_bias + sensitivity_bonus`. Filters out zero-overlap judges. Caps at `max_judges` (default 10), removed by `--all`.
- `Dispatcher` — runs judges in parallel via `ThreadPoolExecutor`. One LLM call per judge, each in a fresh provider instance. Per-judge failures become SKIP verdicts with the error string (the whole run never aborts because one judge crashed).
- `Verifier` — for every reported issue, confirms the cited line exists in the source AND that a category-specific token (from a hard-coded dictionary of hints per category) appears within ±3 lines. Unverified issues are **kept but labeled** — the synthesizer downweights them.
- `Synthesizer` (rule-based) — computes board verdict from verified severities. FAIL if any verified CRITICAL/HIGH, WARN on MEDIUM or vote split, PASS otherwise. Surfaces disagreements instead of collapsing them.

### `bojudges.judges`
- `Judge` (abstract) — orchestrates `tools run → prompt build → LLM call → parse → verify → calibrate`. Every judge emits a `JudgeVerdict`.
- Builtin judges live in `src/bojudges/judges/builtin/<id>/` as `manifest.yaml + persona.md + exemplars.jsonl`. Loaded lazily.
- `registry.JudgeRegistry.from_dir()` — loads every `manifest.yaml` in a tree. Users can point `--judges-dir` at a custom directory to extend the panel.

### `bojudges.rendering`
- `rendering.terminal.print_report` — rich-based interactive output.
- `rendering.markdown.report_to_markdown` — for PR comments and `judgements/*.md`.

### `bojudges.cli`
Typer app. Subcommands: `judge`, `list-judges`, `route`, `schema`, `version`.

## Data contracts

- **JSON schema v1** is the stable contract. Additive changes only within `1.x`; breaking changes bump to `2.x` and live alongside for two minors.
- **`RunManifest.fingerprint()`** — SHA-256 of models + prompt_hashes + exemplars_hashes + temperature + seed. Identical runs produce identical fingerprints. Used by CI gates and eval reproducibility.
- **`Issue.verified`** is the truth of whether we believe the line citation. Consumers (CI, PR comment adapters) should treat unverified issues as low-confidence.

## Concurrency model

- The dispatcher is thread-based. Each judge call is blocking I/O to an LLM provider — threads are fine, and the complexity of async across three SDKs isn't worth it yet.
- `max_workers` defaults to 6. Providers may rate-limit; judges already handle errors as SKIP verdicts, so a rate-limited judge doesn't break the run.
- The verifier runs in the calling thread of each judge — it's cheap (string scans) and has no I/O.

## Prompt caching strategy

- System block is always cache-eligible (`cache=True` in `Message`). Anthropic attaches `cache_control: ephemeral`.
- Long stable user prefix (exemplars, tool findings) is cached when it exceeds the provider's minimum cached-tokens threshold (Anthropic: 1024 tokens for Sonnet).
- Cache is keyed per (provider, judge system prompt, exemplars hash) — sharing the cache across judges is not a goal and is not possible because personas differ.
- `cache_read_tokens` and `cache_create_tokens` are tracked in `JudgeVerdict`; aggregate hit rate is visible in the run manifest.

## Eval harness

- `evals/datasets/<name>/ground_truth.yaml` + `evals/datasets/<name>/snippets/*.{py,ts,…}`
- `evals/runner.py --dataset <name> --judge <id> --provider mock|anthropic|google|openai`
- Computes precision, recall, F1, verdict accuracy, and Expected Calibration Error (5-bin). Reports JSON to `evals/reports/`.
- The seed dataset (`sqli_seed`) gates Phase 0. With `--provider mock`, the harness validates end-to-end plumbing without LLM calls.

## Why this architecture will not turn into v1

Each of the anti-patterns called out in `memory/project_v1_do_not_retry.md` is structurally prevented:

| v1 failure | v2 prevention |
|------------|---------------|
| Single-context roleplay | `Dispatcher` spawns one real LLM call per judge; personas never share context |
| No evals | `evals/` is first-class, CI-gated, runs are manifest-pinned |
| Emoji-only output | JSON schema is source of truth; unicode is renderer output |
| No tool grounding | `Tool` protocol is a judge's primary input; LLM sees tool findings before it reasons |
| Claude-only distribution | `adapters/` ships 8+ host integrations; core is a plain Python CLI |
| Free-text confidence | `confidence` is a numeric field; calibration runs over eval sets |
| No reproducibility | `RunManifest.fingerprint()` captures everything that affects outputs |
