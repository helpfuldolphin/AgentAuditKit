# AAK v0.1 Claim Contract (Freeze)

Status: Draft for immediate freeze before implementation  
Owner: AAK product lead  
Version: 0.1.0-contract

## Core Product Claim (Canonical)

**AAK makes AI agent decisions replayable, inspectable, and stress-testable without modifying the model.**

## v0.1 Guarantee Statement

AAK v0.1 guarantees deterministic replay of captured execution events and tamper-evident evidence verification under a declared runtime environment.

## v0.1 Does Not Guarantee

- Correctness of model reasoning
- Agent safety or policy alignment
- Completeness of all possible runtime signals
- Deterministic output reproduction for hosted LLM inference
- Governance authority, trust assignment, or compliance certification

## Lane Boundary (Non-Negotiable)

- AAK is Lane B forensic tooling only.
- AAK artifacts are evidence for human review.
- AAK outputs cannot be used to assign authority class or governance trust.
- MathLedger authority logic remains separate in repository, roadmap, language, and product surface.

## Scope Freeze: Stress Profiles (v0.1)

Stress profiles must stay simple, heuristic, transparent, and repeatable:

- `authority`
- `urgency`
- `conflicting-instructions`

Out of scope for v0.1:

- CPF graph richness
- Complex decay/interdependency models
- Research-heavy psychological taxonomies

## Open-Core Floor (Cannot Move to Paid)

The following must remain fully open and standalone:

- Full capture pipeline (SDK + interception)
- Full replay determinism for captured event timelines
- Full hash-chain verification workflow
- Bundle format specification
- Baseline stress runner and built-in profiles

Paid value may be orchestration, collaboration, analytics, and enterprise integrations, but not truth primitives.

## Messaging Guardrails

AAK messaging must sound like practical infrastructure:

- Replayable observability
- Forensic readiness
- Incident audit tooling
- Logging for high-risk automation

AAK messaging must avoid ideological framing:

- "Alignment revolution"
- "Cognitive defense layer"
- "Epistemic authority engine"

## v0.1 Success Metrics (Ship Gate)

- Time to replay one session: `< 60s` from bundle open to readable timeline
- Deterministic replay fidelity: `>= 99%` event-order and hash-consistency over repeated runs in same environment
- Bundle verification time: `< 30s` for reference demo bundle
- Stress-profile reproducibility rate: `>= 95%` same profile produces same flag class/severity pattern under same seed/config

## Scope Reduction Trigger (Week 6)

If deterministic replay cannot be demonstrated across three heterogeneous agent stacks by week 6, v0.1 scope is reduced immediately and non-essential work is deferred.

## Change Control

Any change to this contract requires explicit sign-off from:

1. Product owner
2. Engineering lead
3. Lane-boundary reviewer (MathLedger separation)

Until approved, this contract is treated as canonical for v0.1 planning and implementation.
