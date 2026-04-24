# Adapter development guide

This document is for people adding a new host (a new coding CLI / IDE / agent framework) to the `adapters/` tree.

## The contract

An adapter is **any** mechanism that lets a host invoke `boj judge <file>` and render the output in that host's native UI. That's it.

### MUST

- Invoke `boj judge <file> [flags]` — never reimplement review logic.
- Support at minimum: `--panel`, `--solo`, `--all`, `--format`, `--output`, `--markdown`.
- Propagate `boj`'s exit code (0 / 1 / 2) to the host where possible.
- Document prerequisites (Python, API keys, optional semgrep) in the adapter's `README.md`.

### SHOULD

- Provide a single-word activation (slash command, custom command, alias).
- Render the JSON (`--format json`) natively when the host has richer UI than a terminal.
- Detect PR context and offer to post results via `gh pr comment` when appropriate.
- Respect cost: many hosts run in CI; document how to scope the review (file list, panel filter, max judges).

### MUST NOT

- Fork the persona prompts. Those belong to `boj`.
- Run additional LLM calls "on top of" the board output (no "let me reinterpret the board's findings for you").
- Hide unverified issues silently — surface them, labeled.

## The minimum adapter

Three files:

```
adapters/<host>/
├── README.md              # install + run instructions
├── <host>-config-snippet  # the config or command registration for that host
└── (optional) install.sh  # helper installer
```

That's the whole spec.

## Template: Cursor-style rule adapter

```markdown
---
description: Board of Judges — tool-grounded code review
---

When asked to review, audit, or critique a file, run:

    boj judge <file> --format markdown --markdown judgements/<host>-<timestamp>.md

Show the resulting markdown verbatim. Do not improvise verdicts.
```

## Template: CLI-tool command adapter

```yaml
# e.g. config.yaml for a hypothetical host
commands:
  - name: judge
    command: boj judge $FILE --format markdown --markdown judgements/$TIMESTAMP.md
    args:
      - FILE: required
```

## Template: CI / GitHub Action adapter

See `adapters/github-action/` for a complete example. Key steps:

1. Install `boj` (from PyPI or repo).
2. Detect changed files in the PR / push.
3. Run `boj judge` per file; write reports to `judgements/`.
4. Aggregate a summary and post as PR comment.
5. Set exit code based on aggregate verdict.

## Testing an adapter

Adapter tests go in `tests/adapters/test_<host>.py` and should:

- Verify the adapter's config or skill file points at `boj` (no hand-rolled LLM calls).
- Parse-check any YAML/JSON config for schema validity.
- (Optional) Shell out to the host in a sandbox and confirm it invokes `boj` correctly.

## Models in adapters

Users may want a specific host to use a specific model. Two paths:

1. **Global:** export `BOJ_DEFAULT_MODEL=claude-sonnet-4-6` (set and read at the CLI layer; upcoming in 0.3).
2. **Per-invocation:** `boj judge <file> --model gpt-4.1` — overrides every judge's declared model for that run. Useful in CI.

Judges declare their preferred model in `manifest.yaml`. Respect that default; only override when the user explicitly asks.

## Versioning

Adapter files pin to the `bojudges` major version. If `boj` emits JSON schema v2, adapters that parse JSON need to be revved. The schema version is in `BoardReport.manifest.schema_version`.
