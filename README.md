# Board of Judges

**A multi-agent code review system for Claude Code.** Submit any artifact — code, architecture docs, SQL schemas, Terraform configs, PRDs — and a panel of specialist AI judges reviews it sequentially, each reading what the previous judge found before writing their own verdict. A Chief Synthesizer then distills all verdicts into a final board summary.

Every judge is also independently accessible as a solo agent via Claude Code's native `@agent-name` syntax.

---

## What It Does

- **88 specialist judges** across 9 domains: Security, Engineering, Infrastructure, AI/Data, UX, QA, Domain Specialists, Business/Legal, and Crisis/Support
- **Smart selection**: the coordinator detects your file type and picks the most relevant judges automatically (default cap: 10)
- **Sequential review with context**: each judge reads compressed prior verdicts before writing their own — findings compound
- **Chief Synthesis**: a final summary with verdict table, critical issues, warnings, consensus, and recommended action
- **Persistent reports**: every review saved to `judgements/` as a timestamped markdown file
- **Solo access**: use any judge directly with `@judge-<name>` without running the full board

---

## Requirements

- [Claude Code](https://claude.ai/code) (CLI, desktop app, or IDE extension)
- The repo cloned locally — the `.claude/` directory ships with it

No installation, no dependencies, no API keys beyond your existing Claude Code setup.

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/board-of-judges
cd board-of-judges

# Open in Claude Code, then run a review
/judge path/to/your/file.py
```

That's it. Agents are project-local — they activate the moment you open this directory in Claude Code.

---

## Usage

### Full Board Review

```bash
/judge src/auth/login.py
```

The coordinator detects the file type, selects up to 10 relevant judges ordered by tier, runs them sequentially, then produces a Chief Summary. The full report is saved to `judgements/`.

### Filter by Domain

```bash
# Security judges only
/judge src/auth/login.py --panel security

# Multiple panels
/judge schema.sql --panel database,backend

# All matching judges (removes 10-judge cap)
/judge src/auth/login.py --all
```

### Single Judge

```bash
# Via skill
/judge src/auth/login.py --solo appsec-engineer

# Via native Claude Code agent syntax (no skill needed)
@judge-sec-application-security-appsec-engineer
```

Then describe what you want reviewed in your message.

### Post to GitHub PR

```bash
/judge src/auth/login.py --post-to-pr
```

After saving the report locally, posts the Chief Summary as a comment on the current branch's open PR using `gh`.

### List All Judges

```bash
/list-judges
```

Displays all 98 judges grouped by section with their tags and filenames — useful for finding the right `--solo` or `--panel` target.

---

## Verdict Format

### Individual Judge

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JUDGE — APPLICATION SECURITY (APPSEC) ENGINEER    [TIER 1]
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

### Chief Summary

```
╔══════════════════════════════════════════════════════════╗
║           BOARD OF JUDGES — CHIEF SUMMARY                ║
╚══════════════════════════════════════════════════════════╝

SUBMISSION:     src/auth/login.py
JUDGES:         7  |  DATE: 2026-04-22  |  TIME: 14:32

BOARD VERDICT:  ⚠️ WARN

┌──────────────────────────────────────────┬──────────┬───────┐
│ Judge                                    │ Verdict  │ Score │
├──────────────────────────────────────────┼──────────┼───────┤
│ Principal Systems Architect              │ ✅ PASS  │  7/10 │
│ Application Security Engineer           │ ⚠️ WARN  │  5/10 │
│ Lead Backend Engineer                   │ ⚠️ WARN  │  6/10 │
│ IAM Specialist                          │ ❌ FAIL  │  3/10 │
│ QA Automation Architect                 │ ✅ PASS  │  8/10 │
│ Performance Engineer                    │ ✅ PASS  │  7/10 │
│ CISO                                    │ ⚠️ WARN  │  5/10 │
├──────────────────────────────────────────┼──────────┼───────┤
│ OVERALL BOARD SCORE                      │          │ 5.9/10│
└──────────────────────────────────────────┴──────────┴───────┘

CRITICAL ISSUES (must fix before ship):
1. [IAM] No token rotation — stolen credentials valid indefinitely
2. [Security] JWT in localStorage — XSS exfiltration risk

WARNINGS (fix soon):
3. [Backend] No rate limiting on login endpoint
4. [CISO] No audit log for failed authentication attempts

CONSENSUS:
Security judges unanimously flag token storage. IAM raises this
to a pre-ship blocker. Architecture passes on structure — the
pattern is sound but the implementation is dangerous.

RECOMMENDED ACTION: Fix CRITICAL issues, re-judge security panel.
```

---

## The Judges

### Tier 1 — Foundation (run first, every other judge builds on these)

**Security, Privacy & Compliance** (`--panel security`)
- Application Security (AppSec) Engineer
- Chief Information Security Officer (CISO)
- Cloud Security Architect
- Cryptography & Encryption Specialist
- Defensive Security / Blue Team Lead
- GDPR & Data Privacy Compliance Officer
- Governance, Risk and Compliance (GRC) Lead
- Identity & Access Management (IAM) Specialist
- Offensive Security / Red Team Lead
- Open Source Security & Licensing Auditor
- SOC2 & ISO 27001 Auditor
- Threat Intelligence Analyst

**Engineering & Architecture** (`--panel architecture`)
- Principal Systems Architect
- Lead Backend Engineer
- Frontend Platform Architect
- Distributed Systems Specialist
- Microservices Orchestration Expert
- API Strategy & Governance Lead
- Concurrency & Multithreading Specialist
- Embedded Systems & Firmware Engineer
- Fullstack Generalist Critic
- Legacy Systems Modernization Expert
- Mobile Solutions Architect
- Systems Refactoring Strategist

### Tier 2 — Domain

**Infrastructure, Cloud & Ops** (`--panel infrastructure`)
- Cloud Infrastructure Architect · Containerization & Kubernetes Specialist
- Database Reliability Engineer (DBRE) · DevOps Automation Engineer
- Disaster Recovery & BCP Strategist · Edge Computing Specialist
- FinOps & Cloud Cost Optimizer · Linux Kernel & OS Hardening Expert
- Network Architect (SDN/VPC) · Observability & Telemetry Architect
- Platform Engineer (IDP Specialist) · Site Reliability Engineer (SRE)

**Data Science & AI** (`--panel ai`)
- AI/ML Research Scientist · AI Ethics & Bias Auditor
- AI Product Safety Officer · Computer Vision Specialist
- Data Architect (Big Data/Warehousing) · Data Pipeline & ETL Engineer
- Feature Engineering Specialist · MLOps & Machine Learning Engineer
- NLP Lead · Neural Network Optimization Engineer
- Vector Database & RAG Architect · Quantitative Data Analyst

### Tier 3 — Quality/Ops

**Quality, Testing & Performance** (`--panel testing`)
- QA Automation Architect (SDET) · Chaos Engineering Specialist
- Lead Integration Tester · Manual & Exploratory Tester
- Performance & Load Testing Engineer · Security Regression Tester
- User Acceptance Testing (UAT) Coordinator · Mobile Device Lab Manager

**Product, Design & UX** (`--panel ux`)
- UX Research Lead · UI/UX Visual Critic · Interaction Designer
- Information Architect · Design Systems Architect
- Accessibility (A11y) & Inclusion Specialist
- Customer Journey Mapper · Conversion Rate Optimization Specialist
- Product Strategy Director · Technical Product Manager (TPM)

**Specialized Industry Domains** (`--panel domain`)
- Blockchain & Smart Contract Auditor · Fintech Compliance & Payment Specialist
- Healthcare Systems (HIPAA/HL7) Expert · IoT & Hardware Interaction Specialist
- AR/VR & Spatial Computing Architect · Game Engine & Physics Lead
- EdTech Pedagogical Consultant · E-commerce & Logistics Strategist

### Tier 4 — Strategy

**Business, Legal & Corporate** (`--panel business`)
- Chief Technology Officer (CTO) · Legal & Intellectual Property Counsel
- Engineering Manager (EM) · Technical Business Analyst
- Agile Coach & Scrum Master · Release Train Engineer (RTE)
- Developer Experience (DX) Engineer · Growth & GrowthHacking Engineer
- Corporate Sustainability Auditor · Technical Documentation & Content Lead

**Crisis & Support** (`--panel crisis`)
- Incident Commander · PostMortem & Root Cause Analyst
- Customer Support Engineering Lead · Technical Training & Enablement Lead

---

## Project Structure

```
board-of-judges/
├── .claude/
│   ├── agents/                      # 88 judge agents + synthesizer
│   │   ├── judge-sec-*.md           # Security & Compliance (Tier 1)
│   │   ├── judge-eng-*.md           # Engineering & Architecture (Tier 1)
│   │   ├── judge-infra-*.md         # Infrastructure & Ops (Tier 2)
│   │   ├── judge-ai-*.md            # Data Science & AI (Tier 2)
│   │   ├── judge-ux-*.md            # Product, Design & UX (Tier 3)
│   │   ├── judge-qa-*.md            # Quality & Performance (Tier 3)
│   │   ├── judge-domain-*.md        # Specialized Domains (Tier 3)
│   │   ├── judge-biz-*.md           # Business & Legal (Tier 4)
│   │   ├── judge-crisis-*.md        # Crisis & Support (Tier 4)
│   │   └── judge-synthesizer.md     # Chief Synthesizer
│   └── skills/
│       ├── judge/                   # /judge coordinator
│       ├── bootstrap-judges/        # /bootstrap-judges
│       └── list-judges/             # /list-judges
├── scripts/
│   └── bootstrap_claude_judges.py   # Source of truth for all judge definitions
├── judgements/                      # Saved review reports (timestamped)
├── docs/design.md                   # System design specification
├── CLAUDE.md                        # Claude Code project context
└── README.md
```

---

## Adding or Modifying Judges

`scripts/bootstrap_claude_judges.py` is the single source of truth. Agent files are generated output — edit the script, not the files directly.

**Add a new judge:**
1. Open `scripts/bootstrap_claude_judges.py`
2. Add an entry to the `JUDGES` list with: slug, role name, tier (1–4), tags, expertise bullets, and "what you miss" insight
3. Run `/bootstrap-judges` (or `python scripts/bootstrap_claude_judges.py`)

**Inspect a generated agent:**
```bash
python scripts/bootstrap_claude_judges.py --review judge-sec-application-security-appsec-engineer.md
```

**Preview what would be generated (dry run):**
```bash
python scripts/bootstrap_claude_judges.py --dry-run
```

---

## How Context Is Managed

To prevent context bloat across a large panel, the coordinator compresses verdicts between passes:

- Each judge receives: `[full submission] + [compressed prior verdicts]`
- Compression format: `Judge Name | Verdict | Score | Core Finding (1 sentence)`
- Full verdicts are held by the coordinator and passed to the Chief Synthesizer in one shot

This keeps individual judge prompts lean while preserving synthesis quality.

---

## Saved Reports

Every review is saved to `judgements/` with a timestamped filename:

```
judgements/
├── 2026-04-22-14-32-login-py.md
├── 2026-04-22-15-10-schema-sql.md
└── 2026-04-22-16-45-product-prd.md
```

Each file contains the full individual verdicts followed by the Chief Summary. Reports are plain markdown — diffable, greppable, and committable to git.

---

## Design

The full system design document is at [`docs/design.md`](docs/design.md).

---

## License

MIT
