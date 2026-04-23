# Board of Judges

Multi-agent code review system. 98 specialist AI judges review any artifact and deliver expert verdicts. A Chief Synthesizer distills everything into a final board summary.

## Quick Commands

```bash
# Review a file — smart judge selection (up to 10 judges)
/judge src/auth/login.py

# Restrict to a specific domain
/judge src/auth/login.py --panel security
/judge schema.sql --panel database,backend

# Single judge
/judge src/auth/login.py --solo appsec-engineer

# Run every matching judge (slower)
/judge src/auth/login.py --all

# Post Chief Summary as a GitHub PR comment
/judge src/auth/login.py --post-to-pr

# Use a judge directly (no skill needed)
@judge-sec-application-security-appsec-engineer

# List all available judges
/list-judges

# Regenerate all agent files from role stubs
/bootstrap-judges
```

## How Judge Selection Works

The coordinator detects the file type and activates matching tags:

| File type | Judges activated |
|-----------|-----------------|
| `.py` `.go` `.rs` `.java` | Security, Backend, QA, Performance |
| `.ts` `.tsx` `.jsx` `.css` | Security, Frontend, UX, Accessibility |
| `.sql`, migrations | Security, Backend, Database |
| Architecture docs | Security, Architecture, Strategy |
| PRDs, specs | Product, Legal, Business |
| `Dockerfile`, `*.yaml`, Terraform | Security, DevOps, Infrastructure |

Default cap: 10 judges per review. Use `--all` to remove it.

## Available Judge Sections

| Prefix | Section | Tier |
|--------|---------|------|
| `judge-sec-*` | Security, Privacy & Compliance | 1 — Foundation |
| `judge-eng-*` | Engineering & Architecture | 1 — Foundation |
| `judge-infra-*` | Infrastructure, Cloud & Ops | 2 — Domain |
| `judge-ai-*` | Data Science & AI | 2 — Domain |
| `judge-ux-*` | Product, Design & UX | 3 — Quality/Ops |
| `judge-qa-*` | Quality, Testing & Performance | 3 — Quality/Ops |
| `judge-domain-*` | Specialized Industry Domains | 3 — Quality/Ops |
| `judge-biz-*` | Business, Legal & Corporate | 4 — Strategy |
| `judge-crisis-*` | Crisis & Support | 4 — Strategy |

## Project Layout

```
.claude/
  agents/          88 judge agents + synthesizer (project-local, ships with repo)
  skills/          /judge, /bootstrap-judges, /list-judges skill definitions
scripts/
  bootstrap_claude_judges.py   Source of truth for all judge definitions
judgements/        Timestamped review reports saved here
docs/design.md     Full system design specification
```

## Adding a New Judge

Open `scripts/bootstrap_claude_judges.py` and add an entry to the `JUDGES` list, then run:

```bash
python scripts/bootstrap_claude_judges.py
```

Or via skill: `/bootstrap-judges`

The script is idempotent — re-running updates existing agents without losing manual edits to files not covered by the template.
