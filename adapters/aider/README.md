# Aider adapter

Aider supports custom commands via its `/run` or `!`-prefixed shell calls.

## Quick use (no install needed)

```
!boj judge <file> --format terminal
```

## Custom command (one-time setup)

Add to your aider `~/.aider.conf.yml`:

```yaml
aliases:
  judge: "!boj judge"
```

Now:

```
judge src/auth/login.py
judge src/auth/login.py --panel security
```

## As part of the edit loop

Before Aider commits a change set, run the board:

```
!boj judge <file> --output /tmp/bojreport.json --format terminal
```

If the board returns exit code 1 (FAIL), revert with `/undo` before committing.

## Tip

Aider runs a single main model. You can keep Aider on one model (e.g. GPT-4)
while having the board route judges to Claude/Gemini/GPT independently —
set per-judge `model:` in the manifests.
