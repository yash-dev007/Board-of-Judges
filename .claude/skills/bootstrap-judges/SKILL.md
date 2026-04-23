---
name: bootstrap-judges
description: >
  Generates all Claude Code judge agent files from role stubs.
  Run once to populate .claude/agents/ with 87+ specialist judge personas.
  Usage: /bootstrap-judges [--dry-run] [--review <agent-filename>]
---

# Bootstrap Judges

You are the **Bootstrap Coordinator**. Your job is to generate or inspect Claude Code
judge agent files by running the bootstrap script.

---

## Step 1 — Parse Flags

- `--dry-run`: preview filenames without writing files
- `--review <filename>`: display the content of an existing agent file
- (no flags): generate all agents

---

## Step 2 — Execute

Run the bootstrap script from the project root:

```bash
python scripts/bootstrap_claude_judges.py [flags]
```

Pass any user-provided flags through to the script directly:
- `/bootstrap-judges` → `python scripts/bootstrap_claude_judges.py`
- `/bootstrap-judges --dry-run` → `python scripts/bootstrap_claude_judges.py --dry-run`
- `/bootstrap-judges --review judge-sec-application-security-appsec-engineer.md` → `python scripts/bootstrap_claude_judges.py --review judge-sec-application-security-appsec-engineer.md`

---

## Step 3 — Report

After the script completes:
- Report how many agents were generated (or would be generated with `--dry-run`)
- Confirm the output directory: `.claude/agents/`
- If `--review` was used, display the file content the script printed

---

## Notes

- Idempotent: re-running overwrites existing agents with fresh content
- To regenerate a single agent: `/bootstrap-judges --review <filename>` to inspect,
  then delete and re-run to regenerate
- After bootstrapping, verify with `/list-judges`
