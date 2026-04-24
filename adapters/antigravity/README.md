# Google Antigravity adapter

Antigravity (Google's agentic IDE/CLI platform) runs tools via MCP servers or
explicit command declarations. Integrate Board of Judges as either.

## Option 1 — Command entry (simplest)

Add to your Antigravity project config (`.antigravity/commands.yaml` or
whatever location your Antigravity version uses; check current docs):

```yaml
commands:
  - name: judge
    description: "Run the Board of Judges panel review on a file."
    command: boj judge $FILE --format markdown --markdown judgements/antigravity-$TIMESTAMP.md
    arguments:
      - name: FILE
        required: true
        description: "Path to the file to review."
    capture: stdout
```

## Option 2 — As an MCP server

Board of Judges will ship a first-party MCP server in v0.3. For now, use Option 1.

## Model config

Antigravity often defaults to Gemini. Judges targeting `model: gemini-2.5-pro`
will use Gemini for the LLM call. Other judges (`claude-*`, `gpt-*`) will still
work if the matching API key is set in the Antigravity environment.

## Sample invocation

```
/judge src/auth/login.py
```

Antigravity runs the command, captures stdout, and renders the markdown.
