# OpenAI Codex adapter

Register Board of Judges as a Codex agent. Two integration paths:

## Path A — AGENTS.md (recommended)

Place `AGENTS.md` in your project root or import from this directory:

```bash
cp adapters/codex/AGENTS.md AGENTS.md
```

Codex will pick up the instructions and know to run `boj judge <file>` when
the user asks for a review.

## Path B — Tool definition for agentic Codex

If you use Codex as an agent with tool-use enabled, register `boj` as a tool:

```json
{
  "type": "function",
  "function": {
    "name": "code_review_panel",
    "description": "Runs the Board of Judges multi-specialist code review on a file or patch.",
    "parameters": {
      "type": "object",
      "required": ["target"],
      "properties": {
        "target":       {"type": "string", "description": "File path to review."},
        "panel":        {"type": "string", "description": "Comma-separated tag filter."},
        "solo":         {"type": "string", "description": "Run a single judge by id."},
        "allow_all":    {"type": "boolean", "description": "Remove the 10-judge cap."},
        "format":       {"type": "string", "enum": ["json", "markdown", "terminal"]}
      }
    }
  }
}
```

The handler shells out:
```bash
boj judge <target> [--panel ...] [--solo ...] [--all] --format <format>
```

## Configure a model

To use Codex/GPT as the judge model, set `model: gpt-4.1` in a judge's
manifest.yaml. Export `OPENAI_API_KEY` in the environment.
