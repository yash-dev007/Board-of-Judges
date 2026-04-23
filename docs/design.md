# Board of Judges — System Design Spec
**Date:** 2026-04-22
**Status:** Approved for implementation
**Author:** Brainstormed with Claude Code

---

## 1. Overview

The Board of Judges is a multi-agent code review system built on Claude Code. Specialized AI agents — each a domain expert — review any submitted artifact (code, architecture docs, business specs, PRDs, infra configs, or anything else) and deliver expert verdicts sequentially, each reading what the previous judge said before writing their own verdict. A Chief Synthesizer then distills all verdicts into a final board summary.

Every judge is also independently accessible as a solo agent via Claude Code's native `@agent-name` syntax, making them useful for targeted, day-to-day reviews without running the full board.

---

## 2. Goals

- Provide reliable, multi-perspective technical review for any artifact
- Make each of the 87+ specialist roles independently accessible as a Claude Code agent
- Auto-generate full agent personas from role stubs via a single bootstrap command
- Deliver individual judge verdicts + a synthesized Chief Summary per review
- Save all verdicts locally as timestamped markdown reports
- Cap review time by limiting default board size to 10 judges max

---

## 3. Non-Goals

- This is not a linting or static analysis tool (no AST parsing)
- This is not a CI/CD gate (no automatic pipeline triggers)
- This does not replace human code review — it augments it
- This does not run autonomously without user invocation

---

## 4. Architecture

```
User: /judge <target> [--panel X] [--solo X] [--all] [--post-to-pr]
         │
         ▼
  ┌─────────────┐
  │ Coordinator │  reads target, detects type, invokes Selector
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │   Selector  │  picks ≤10 most relevant judges, orders by tier
  └──────┬──────┘
         │
         ▼
  Tier 1 — Foundation (Security, Architecture)
  each judge reads: [submission + compressed prior verdicts]
         │
         ▼
  Tier 2 — Domain (Backend, Frontend, Data, Infra…)
         │
         ▼
  Tier 3 — Quality/Ops (QA, Performance, SRE, Observability…)
         │
         ▼
  Tier 4 — Strategy (CTO, Legal, Product, TPM…)
         │
         ▼
  ┌───────────────────┐
  │ Chief Synthesizer │  reads all verdicts → final summary
  └─────────┬─────────┘
            │
     ┌──────┴───────┐
     ▼              ▼
Terminal        judgements/
output          YYYY-MM-DD-HH-MM-<filename>.md
                (+ optional GitHub PR comment via --post-to-pr)
```

---

## 5. Components

| Component | Type | Location | Purpose |
|-----------|------|----------|---------|
| `/judge` | Claude Code skill | `.claude/skills/judge/SKILL.md` | Coordinator entry point |
| `/bootstrap-judges` | Claude Code skill | `.claude/skills/bootstrap-judges/SKILL.md` | Auto-generates all agent files |
| `/list-judges` | Claude Code skill | `.claude/skills/list-judges/SKILL.md` | Lists all judges by section + tags |
| `judge-*.md` (87+) | Agent files | `.claude/agents/` | One agent per role |
| `judge-synthesizer.md` | Agent file | `.claude/agents/` | Chief Summary writer |
| `judgements/` | Directory | Project root | Timestamped verdict reports |

---

## 6. File Structure

```
Board of Judges/
├── Roles_Directory.md
├── Section_I_Engineering__Architecture_The_Builders/
│   └── Principal_Systems_Architect.md  (role stubs, source of truth)
├── ... (8 more section directories)
│
├── .claude/
│   ├── skills/
│   │   ├── judge/
│   │   │   └── SKILL.md
│   │   ├── bootstrap-judges/
│   │   │   └── SKILL.md
│   │   └── list-judges/
│   │       └── SKILL.md
│   └── agents/
│       ├── judge-eng-principal-systems-architect.md
│       ├── judge-eng-lead-backend-engineer.md
│       ├── judge-sec-appsec-engineer.md
│       ├── judge-sec-ciso.md
│       ├── ... (87+ agents)
│       └── judge-synthesizer.md
│
├── judgements/
│   └── 2026-04-22-14-32-login-py.md
│
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-22-board-of-judges-design.md
```

---

## 7. Agent File Format

Every judge agent is fully self-contained. It does not depend on the Coordinator to function — it works equally when invoked solo via `@agent-name` or as part of the board.

```markdown
---
name: Judge - Application Security Engineer
description: Reviews code, APIs, and systems for vulnerabilities,
             auth flaws, injection risks, and OWASP Top 10. Tier 1.
---

# Identity
You are the **Application Security Engineer** on the Board of Judges.
Your mandate is to find what breaks, leaks, or gets exploited before
an attacker does. You are the last line of defense before code ships.

## Domain Expertise
- OWASP Top 10 vulnerability patterns
- Authentication and session management flaws
- Injection attacks (SQL, command, LDAP, XSS)
- Insecure deserialization and dependency vulnerabilities
- Secrets management and hardcoded credential detection
- API security (rate limiting, auth bypass, BOLA/BFLA)
- Cryptographic implementation weaknesses
- Supply chain and third-party dependency risks

## Judgment Tier
**Tier 1 — Foundation.** You review early. Every other judge builds
on the assumption that your security concerns are visible.

## Selection Tags
`security`, `backend`, `frontend`, `api`, `auth`, `database`,
`code`, `infrastructure`, `devops`, `secrets`, `dependencies`

## What You Look For That Others Miss
Input validation gaps that look harmless until chained with another
vulnerability. Trust boundaries developers assume are enforced but
aren't. Auth logic that works in the happy path but fails at edges.

## Verdict Format
You are reviewing the submission shown above.
Read all preceding judge verdicts (if any) before writing yours.

Structure your verdict exactly as:

1. **Verdict:** PASS | WARN | FAIL
2. **Core Finding:** Your single most critical observation (1–2 sentences)
3. **Detailed Analysis:** Specific issues, line references where possible
4. **Recommendations:** Concrete fixes, not generic advice
5. **Score:** X/10

Be direct. Name the vulnerability class. Give the attack scenario.
```

---

## 8. Agent Naming Convention

All agent filenames use a section prefix + slugified role name:

| Section prefix | Section |
|---------------|---------|
| `eng` | Engineering & Architecture |
| `infra` | Infrastructure, Cloud & Ops |
| `sec` | Security, Privacy & Compliance |
| `ai` | Data Science & AI |
| `ux` | Product, Design & UX |
| `qa` | Quality, Testing & Performance |
| `domain` | Specialized Industry Domains |
| `biz` | Business, Legal & Corporate |
| `crisis` | Crisis & Support |

Examples:
```
judge-sec-appsec-engineer.md
judge-eng-principal-systems-architect.md
judge-qa-automation-architect-sdet.md
judge-biz-chief-technology-officer.md
```

---

## 9. Tier Assignment

| Section | Tier | Rationale |
|---------|------|-----------|
| Security, Privacy & Compliance | 1 — Foundation | Fatal flaws must surface first |
| Engineering & Architecture | 1 — Foundation | Structural issues frame everything |
| Infrastructure, Cloud & Ops | 2 — Domain | Operational context after architecture |
| Data Science & AI | 2 — Domain | Domain-specific after structure |
| Quality, Testing & Performance | 3 — Quality/Ops | Build on domain findings |
| Product, Design & UX | 3 — Quality/Ops | User-facing concerns after technical |
| Specialized Industry Domains | 3 — Quality/Ops | Niche expertise after core |
| Business, Legal & Corporate | 4 — Strategy | Big-picture lens last |
| Crisis & Support | 4 — Strategy | Incident/risk framing last |

---

## 10. Smart Selector Logic

The Coordinator detects the submission type and activates the matching tag set. The Selector then scores all 87 agents against the active tags, ranks by score, keeps the top 10 (or fewer if not enough qualify), and sorts by tier within that set.

| Submission type | Tags activated |
|----------------|---------------|
| Python / Go / Rust code | `backend`, `security`, `testing`, `performance` |
| React / TypeScript / CSS | `frontend`, `accessibility`, `security`, `testing` |
| SQL / DB schema | `database`, `security`, `backend`, `performance` |
| Architecture doc | `architecture`, `system-design`, `security` |
| PRD / business spec | `product`, `legal`, `strategy`, `business` |
| CI/CD / infra config | `devops`, `security`, `infrastructure` |
| Smart contract | `blockchain`, `security`, `legal` |
| Unknown / fallback | `architecture`, `security`, `strategy` |

**Board size cap:** Maximum 10 judges per review by default. Use `--all` to remove the cap and run every matching judge (slower, more expensive).

---

## 11. Invocation Syntax

```bash
# Full board, smart selection (≤10 judges)
/judge src/auth/login.py

# Force a specific panel
/judge src/auth/login.py --panel security

# Multi-panel
/judge src/auth/login.py --panel security,backend

# Single judge only (via skill)
/judge src/auth/login.py --solo appsec-engineer

# Single judge (native Claude Code — no skill needed)
@judge-sec-appsec-engineer   # then describe what to review

# Remove the 10-judge cap
/judge src/auth/login.py --all

# Also post Chief Summary as GitHub PR comment
# (uses `gh pr view --json number` to find the current branch's open PR)
/judge src/auth/login.py --post-to-pr

# No target = judges the file you describe in your next message
/judge
```

---

## 12. Verdict Format

### Individual Judge Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JUDGE #3 — Application Security Engineer          [TIER 1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VERDICT: ⚠️ WARN

CORE FINDING:
JWT tokens stored in localStorage — vulnerable to XSS exfiltration.
Session expiry hardcoded at 30 days with no refresh rotation.

DETAILED ANALYSIS:
Login handler at line 47 writes token directly to localStorage.
Any XSS vector on this domain can exfiltrate it. 30-day expiry
means a stolen token is valid for weeks with no revocation path.

RECOMMENDATIONS:
1. Move JWT to httpOnly cookie — inaccessible to JavaScript
2. Implement refresh token rotation (short-lived access tokens)
3. Add Content-Security-Policy header to reduce XSS surface

SCORE: 5/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Chief Synthesizer Output

```
╔══════════════════════════════════════════════════════════╗
║           BOARD OF JUDGES — CHIEF SUMMARY                ║
╚══════════════════════════════════════════════════════════╝

SUBMISSION:     src/auth/login.py
JUDGES:         7  |  DATE: 2026-04-22  |  TIME: 14:32

BOARD VERDICT:  ⚠️ WARN

┌──────────────────────────────────────┬──────────┬───────┐
│ Judge                                │ Verdict  │ Score │
├──────────────────────────────────────┼──────────┼───────┤
│ Principal Systems Architect          │ ✅ PASS  │  7/10 │
│ Application Security Engineer        │ ⚠️ WARN  │  5/10 │
│ Lead Backend Engineer                │ ⚠️ WARN  │  6/10 │
│ IAM Specialist                       │ ❌ FAIL  │  3/10 │
│ QA Automation Architect              │ ✅ PASS  │  8/10 │
│ Performance Engineer                 │ ✅ PASS  │  7/10 │
│ CISO                                 │ ⚠️ WARN  │  5/10 │
├──────────────────────────────────────┼──────────┼───────┤
│ OVERALL BOARD SCORE                  │          │ 5.9/10│
└──────────────────────────────────────┴──────────┴───────┘

CRITICAL ISSUES (must fix before ship):
1. [IAM] No token rotation — stolen credentials valid indefinitely
2. [Security] JWT in localStorage — XSS exfiltration risk

WARNINGS (fix soon):
3. [Backend] No rate limiting on login endpoint
4. [CISO] No audit log for failed authentication attempts

CONSENSUS:
Security judges unanimously flag token storage. Backend and IAM
agree this is a pre-ship blocker. Architecture passes on structure —
the pattern is sound but the implementation details are dangerous.

RECOMMENDED ACTION: Fix CRITICAL issues, re-judge security panel.
```

---

## 13. Context Management (Anti-Snowball)

To prevent context bloat as judges chain, the Coordinator compresses verdicts between passes:

- Each judge receives: `[full submission] + [compressed prior verdicts]`
- Compression: prior verdicts are reduced to `Judge Name | Verdict | Score | Core Finding (1 sentence)` bullet list
- Full raw verdicts are stored in memory by the Coordinator, not passed forward
- The Chief Synthesizer receives all full raw verdicts at the end (single large context, one-shot synthesis)

---

## 14. Bootstrap Generator

`/bootstrap-judges` generates all 87 agent files from the existing role stubs.

**Process:**
1. Walk all 9 Section directories, collect every `.md` stub file
2. For each role: read name + primary objective + section
3. Generate full agent definition using the template in Section 7
4. Assign tier based on section (Section 9 of this doc)
5. Write to `.claude/agents/judge-<prefix>-<slug>.md`
6. Process in batches of 10, pause for spot-check between batches
7. Idempotent — re-running updates files without destroying manual edits

**Flags:**
```
/bootstrap-judges              # generate all 87 agents
/bootstrap-judges --review X   # regenerate one specific agent
/bootstrap-judges --dry-run    # preview names without writing files
```

---

## 15. Persistence

All reviews saved to `judgements/` in the project root:

```
judgements/
├── 2026-04-22-14-32-login-py.md
├── 2026-04-22-15-10-schema-sql.md
└── 2026-04-22-16-45-product-prd.md
```

Each file contains: full individual verdicts + Chief Summary in one markdown document. These are plain markdown files — diffable, greppable, committable to git if desired.

---

## 16. Known Constraints & Mitigations

| Constraint | Mitigation |
|-----------|-----------|
| Sequential is slow at scale | Default cap of 10 judges; `--all` opt-in for full board |
| Context snowball across 10+ judges | Verdict compression between passes (Section 13) |
| 87 agent files hard to browse | `/list-judges` skill + section prefix naming |
| Bootstrap quality varies | Batch of 10 + spot-check pauses + `--review` flag |
| Cost unpredictable | `--dry-run` on bootstrap; selector cap controls review cost |

---

## 17. Implementation Order

1. **Phase 1 — Foundation**
   - Write `/bootstrap-judges` skill
   - Run it to generate all 87 agent files
   - Manually spot-check 5–10 agents for quality

2. **Phase 2 — Core Review Flow**
   - Write `/judge` Coordinator skill
   - Write `judge-synthesizer.md` agent
   - Test with a single file + 3 judges

3. **Phase 3 — Selector & Panels**
   - Implement smart tag-based selector logic in Coordinator
   - Add `--panel`, `--solo`, `--all` flags
   - Test with 5+ different submission types

4. **Phase 4 — Polish**
   - Write `/list-judges` skill
   - Implement `--post-to-pr` GitHub integration
   - Add `judgements/` persistence
   - End-to-end test with full board on a real project

---

## 18. Success Criteria

- [ ] `/bootstrap-judges` generates all 87 agent files in under 5 minutes
- [ ] `/judge` on a Python file selects the right judges and runs them sequentially
- [ ] Each judge's verdict references previous judges' findings
- [ ] Chief Summary accurately reflects all individual verdicts
- [ ] `@judge-sec-appsec-engineer` works solo with no skill invocation
- [ ] `--panel`, `--solo`, `--all` flags all behave correctly
- [ ] Verdicts saved to `judgements/` with correct filenames
- [ ] Full board review on a 200-line file completes without context errors
