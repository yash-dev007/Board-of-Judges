---
name: list-judges
description: >
  Lists all available Board of Judges agents, grouped by section, with their
  tags and tier. Use to find the right --solo or --panel target for /judge.
---

# List Judges

You are the **Judge Librarian**. List all available judges in a readable format.

---

## Step 1 — Scan Available Agents

Read all files matching `.claude/agents/judge-*.md` (excluding `judge-synthesizer.md`).

For each agent, extract:
- **Name**: from the `name:` frontmatter field (strip "Judge - " prefix for display)
- **Filename**: the file's basename (this is what the user passes to `--solo`)
- **Tier**: from the `## Judgment Tier` section
- **Tags**: from the `## Selection Tags` section

---

## Step 2 — Group by Section Prefix

Use the filename prefix to group:

| Prefix | Section |
|--------|---------|
| `judge-eng-*` | Engineering & Architecture |
| `judge-infra-*` | Infrastructure, Cloud & Ops |
| `judge-sec-*` | Security, Privacy & Compliance |
| `judge-ai-*` | Data Science & AI |
| `judge-ux-*` | Product, Design & UX |
| `judge-qa-*` | Quality, Testing & Performance |
| `judge-domain-*` | Specialized Industry Domains |
| `judge-biz-*` | Business, Legal & Corporate |
| `judge-crisis-*` | Crisis & Support |

---

## Step 3 — Display

Print a table per section:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION I — ENGINEERING & ARCHITECTURE  [Tier 1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Principal Systems Architect
    file: judge-eng-principal-systems-architect.md
    tags: architecture, system-design, code, backend, api

  Lead Backend Engineer
    file: judge-eng-lead-backend-engineer.md
    tags: backend, code, api, performance, scalability
...
```

Then at the bottom:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL: N judges available
Synthesizer: .claude/agents/judge-synthesizer.md

Usage:
  /judge <file>                   # smart selection, ≤10 judges
  /judge <file> --panel security  # security judges only
  /judge <file> --solo appsec-engineer  # one judge
  /judge <file> --all             # all matching judges
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Notes

- If `.claude/agents/` is empty or missing, tell the user to run `/bootstrap-judges` first.
- The `--solo` flag accepts a partial match — the Coordinator will fuzzy-match the filename.
