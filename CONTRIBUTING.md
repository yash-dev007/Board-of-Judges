# Contributing

Thanks for your interest. This is a measurement-first project: every change that affects review quality must be accompanied by an eval run that proves it's not a regression.

## Dev setup

```bash
git clone https://github.com/yash-dev007/board-of-judges
cd board-of-judges
uv sync --all-extras --dev
uv run pytest
```

All tests are offline — they use `MockProvider` and don't need API keys.

To run with a real model:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run boj judge src/bojudges/cli/main.py
```

## Repo tour

- `src/bojudges/` — the core engine. Pydantic schemas, provider abstractions, tools, judges, CLI. Most changes live here.
- `src/bojudges/judges/builtin/` — one directory per judge: `manifest.yaml`, `persona.md`, `exemplars.jsonl`.
- `adapters/` — thin shims for each coding CLI. Tiny; add a new host here.
- `evals/` — benchmark datasets and runner. **Every quality claim must cite a number from here.**
- `tests/` — pytest, offline.
- `docs/` — architecture, plan, adapter guide.

## Adding a new judge

1. Create `src/bojudges/judges/builtin/<judge-id>/`:
   - `manifest.yaml` — id, name, tier, tags, model, tools, calibration.
   - `persona.md` — system prompt. Lead with "What you look for that others miss" and "What you do NOT flag".
   - `exemplars.jsonl` — at minimum 2 worked examples (one FAIL, one PASS).
2. Add at least **10 eval snippets** in `evals/datasets/<judge-domain>_seed/snippets/` with a `ground_truth.yaml`.
3. Run `uv run python evals/runner.py --dataset <name> --judge <id> --provider mock` to confirm plumbing.
4. Run with a real provider. Record the numbers in `BENCHMARK.md` with date + model ID.
5. If the judge passes the Phase 0 gate (P≥0.70, R≥0.60, ECE≤0.15), open a PR. Reviewers will re-run.

## Adding a new adapter

See `docs/adapters.md`. A new adapter is typically ~3 files in `adapters/<host>/`:
- `README.md` — install + run
- the host's config / skill file
- (optional) an installer

Do NOT fork the persona prompts. Adapters must invoke `boj` and render its output.

## Adding a new provider

1. Implement `bojudges.providers.base.Provider` in `src/bojudges/providers/<name>_provider.py`:
   - `generate(messages, model, …) -> LLMResponse`
   - `cost_usd(response) -> float`
2. Register in `providers/registry.py`.
3. Add at least one smoke test in `tests/providers/` (offline, mocked HTTP).
4. Update `docs/architecture.md` and `BENCHMARK.md`.

## Running evals with real models

Costs money. Real numbers ship as PR comments on `BENCHMARK.md`, not in code reviews.

```bash
# Full sweep of all judges × all datasets × default providers
uv run python evals/runner.py --dataset sqli_seed --judge sec-appsec-injection
```

## Schema changes

The JSON schema is the contract. Do NOT make breaking changes to `Issue`, `JudgeVerdict`, `BoardReport`, or `RunManifest` without bumping `bojudges.__schema_version__` and publishing a migration note.

Adding a new optional field with a default? Fine — it's additive, schema stays `1.x`.

Removing a field, renaming a field, changing a type? Breaking — goes to `2.x` and lives alongside `1.x` for two minors.

## Code style

- `ruff check .` — lint clean
- `mypy src` — typed clean
- `pytest` — all green
- No comments explaining what obvious code does; a comment is justified only when `why` is non-obvious.
- Pydantic everywhere at system boundaries. No naked dicts on external surfaces.
- Files under 400 lines where reasonable. Break up large files into module directories.

## Disagree with the design?

Open an issue first. The `docs/v2_plan.md` document is the design memory — it lists what we explicitly chose and what we explicitly ruled out. Bring evidence; respond to the counter-arguments documented there.

## Security

Never commit API keys, `.env`, or `evals/reports/*_real_*.json` that contain full submissions. See `.gitignore`.

If you find a security issue in `boj` itself, email instead of filing a public issue.
