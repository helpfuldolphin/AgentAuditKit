# AAK v0.1 Strategy

This strategy operationalizes the v0.1 claim contract into an execution and monetization plan.

## Wedge Positioning

**AAK makes AI agent decisions replayable, inspectable, and stress-testable without modifying the model.**

One-line product description:
Deterministic replay and stress-testing harness for agent execution events.

## Target Buyers (Early)

- SOC and security engineering teams
- AI startups deploying tool-using agents
- Red-team consultants and security assessors
- Cyber insurance and underwriting workflows

Avoid as primary early segment:

- Alignment labs
- Theoretical research groups
- Frontier-model orgs seeking novel safety science

## Product Voice

Use practical language:

- "Forensic readiness"
- "Replayable observability"
- "Audit-ready evidence bundles"
- "Tamper-evident capture"

Avoid narrative inflation:

- No "AI civilization governance"
- No "alignment substrate" framing
- No ideological claims

## Open-Core and Paid Boundary

### Open Core (always open)

- Capture SDK and interception
- Event schema and bundle spec
- Replay determinism primitives
- Hash verification and standalone verifier
- Baseline stress runner and base profiles

### Paid Layer

- Hosted dashboard and artifact lifecycle
- Multi-run diff analytics and drift tracking
- Team workflows, approvals, and case management
- Enterprise exports and policy packs
- Integrations: SIEM/SOC/SSO/RBAC/support SLAs

Design rule:
Paid features orchestrate decisions around evidence. They do not replace evidence truth mechanics.

## Execution Plan (Pre-Week + 12 Weeks)

### Pre-Week (Week 0): Contract Freeze

- Freeze `docs/AAK_V0_1_CLAIM_CONTRACT.md`
- Publish explicit v0.1 in-scope / out-of-scope list
- Confirm lane-boundary review with MathLedger guardrails

Exit criteria:

- Canonical claim approved
- Stress-profile scope approved
- Open-core floor approved

### Weeks 1-2: Product Contract Hardening

- Finalize event, manifest, and bundle schema contract
- Resolve naming/consistency issues in demo and docs
- Implement and freeze top-level CLI surface (`capture`, `replay`, `stress`)

Exit criteria:

- All contracts versioned
- CLI commands stable for v0.1

### Weeks 3-6: Replay + Stress Core

- Implement replay timeline engine
- Implement stress runner with profiles:
  - `authority`
  - `urgency`
  - `conflicting-instructions`
- Add deterministic artifact diffing for repeat runs

Exit criteria:

- Repeatability tests pass in CI
- Stress outputs are transparent and explainable

### Weeks 7-9: Pilot Readiness

- Harden installer and runtime docs
- Ship one reproducible end-to-end demo case
- Add IR/red-team evidence pack workflows from templates

Exit criteria:

- Buyer can run capture -> verify -> replay -> stress in one session
- Onboarding time under 60 minutes

### Weeks 10-12: Revenue Motion

- Land 2-3 paid pilot engagements
- Convert at least 1 pilot to recurring hosted workflow
- Package service offerings:
  - incident evidence pack engagement
  - red-team replay audit engagement

Exit criteria:

- At least one repeatable paid motion
- Product telemetry informs paid roadmap

## v0.1 Measurable Success Criteria

- Time to replay one session: `< 60s`
- Replay fidelity under fixed environment: `>= 99%`
- Bundle verification time on reference bundle: `< 30s`
- Stress profile reproducibility rate: `>= 95%`

These metrics are required for v0.1 quality gate.

## MathLedger Protection Rules (Fixed)

1. Separate repos, ownership, and release lanes
2. Separate marketing language and value props
3. No authority crossover from AAK artifacts
4. Ring-fenced engineering capacity for MathLedger core

## Immediate Next Actions

1. Freeze and sign off the claim contract
2. Define CLI command contracts and options
3. Write acceptance tests for replay and stress reproducibility
4. Prepare first pilot package and pricing assumptions
