# Adapters

Board of Judges is a **tool-agnostic** review engine. The actual work — routing, panel selection, tool grounding, LLM calls, verification, synthesis — happens in the `boj` Python CLI. Adapters are thin shims that teach each coding CLI how to invoke `boj` and render its output natively.

## Why thin adapters?

- **Consistent behavior.** Quality is uniform across hosts; host quirks don't bleed in.
- **Provider-independent.** A judge can run on Claude, Gemini, or GPT regardless of which coding CLI invokes it.
- **Easy to add a new host.** Most adapters are <100 lines.

## Supported hosts

| Host | Status | Path | Invocation |
|------|--------|------|------------|
| Claude Code | ✅ ready | [claude-code/](claude-code/) | `/judge <file>` (v2 skill calls `boj`) |
| Gemini CLI | ✅ ready | [gemini-cli/](gemini-cli/) | `/judge <file>` |
| OpenAI Codex | ✅ ready | [codex/](codex/) | via AGENTS.md + tool |
| Google Antigravity | ✅ ready | [antigravity/](antigravity/) | config entry |
| Aider | ✅ ready | [aider/](aider/) | `/judge <file>` custom command |
| Cursor | ✅ ready | [cursor/](cursor/) | `.cursorrules` |
| Continue.dev | ✅ ready | [continue/](continue/) | `config.json` custom command |
| GitHub Copilot CLI | ✅ ready | [github-copilot-cli/](github-copilot-cli/) | alias + shell function |
| GitHub Action | ✅ ready | [github-action/](github-action/) | `action.yaml` |

Plain terminal: `boj judge <file>` works everywhere Python runs.

## Adding a new adapter

A new adapter must answer three questions:

1. **How does the host invoke `boj`?** A slash command, a CLI alias, a tool definition, a config entry — pick the host's idiomatic way.
2. **How is the output rendered?** `boj` emits JSON on `--format json`. Most hosts just show the terminal output; richer hosts (IDEs) can parse the JSON for inline comments.
3. **How are API keys configured?** Document the host-specific way to expose `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` / `OPENAI_API_KEY`.

Copy `adapters/aider/` as a template — it's the simplest.

## Contract for adapters

Every adapter MUST:

- Invoke `boj judge <file> [flags]` — never reimplement the review loop.
- Leave artifacts in `judgements/` alone — they're the canonical record.
- Expose the standard flags: `--panel`, `--solo`, `--all`, `--output`, `--markdown`, `--format`.
- Surface the exit code: `boj` returns 1 on `FAIL` verdict, 0 on `PASS`/`WARN`.

Every adapter SHOULD:

- Provide a single-word activation (slash command, custom command, etc.).
- Render the JSON report in the host's native UI where possible.
- Post to GitHub PR if a PR context is detectable (via `gh` or the host's PR API).
