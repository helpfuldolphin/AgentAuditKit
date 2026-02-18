# AAK v0.1 Implementation Backlog

Status: Execution artifact  
Source of truth: `docs/AAK_V0_1_CLAIM_CONTRACT.md`  
Scope: v0.1 only (`capture -> replay -> verify -> stress -> export`)

## Non-Negotiable Scope Guard

Out of scope for v0.1:

- CPF richness and decay matrices
- Adaptive analytics loops
- TDA/convergence index systems
- "AI audits AI" autonomous governance features

If requested during execution, create a v0.2 backlog item and do not expand v0.1.

## Sequencing Overview

| Epic | Window | Depends On | Exit Gate |
|------|--------|------------|-----------|
| `AAK-E0` Contract Freeze | Week 0 | None | Claim + boundary signoff complete |
| `AAK-E1` Capture Contract Hardening | Weeks 1-2 | `AAK-E0` | Capture invariants pass in CI |
| `AAK-E2` CLI Contract | Weeks 1-2 | `AAK-E0` | `capture/replay/stress` CLI stable |
| `AAK-E3` Replay Core | Weeks 3-4 | `AAK-E1`, `AAK-E2` | Deterministic replay gate passes |
| `AAK-E4` Stress Runner v0.1 | Weeks 5-6 | `AAK-E3` | Reproducibility gate passes |
| `AAK-E5` Evidence and Export Ops | Weeks 7-9 | `AAK-E3`, `AAK-E4` | End-to-end operator workflow passes |
| `AAK-E6` Pilot Readiness | Weeks 10-12 | `AAK-E5` | Pilot package ready for first customers |

## Epic Backlog

## `AAK-E0` Contract Freeze (Week 0)

Objective: freeze claims and boundaries before feature work.

### Stories

| Story ID | Story | Dependencies |
|----------|-------|--------------|
| `AAK-S001` | Finalize and approve v0.1 claim contract | None |
| `AAK-S002` | Freeze open-core floor and paid boundary | `AAK-S001` |
| `AAK-S003` | Freeze stress profile scope (`authority`, `urgency`, `conflicting-instructions`) | `AAK-S001` |

### Acceptance Tests

1. `docs/AAK_V0_1_CLAIM_CONTRACT.md` contains canonical claim, non-claims, open-core floor, and change-control section.
2. Contract includes week-6 scope-reduction trigger.
3. Any proposed v0.1 scope addition without signoff is rejected.

## `AAK-E1` Capture Contract Hardening (Weeks 1-2)

Objective: stabilize event capture and evidence schema primitives.

### Stories

| Story ID | Story | Dependencies |
|----------|-------|--------------|
| `AAK-S101` | Version and freeze event schema contract | `AAK-E0` |
| `AAK-S102` | Version and freeze manifest/bundle schema contract | `AAK-S101` |
| `AAK-S103` | Resolve demo/doc field consistency issues (`bundle_id` naming and references) | `AAK-S102` |
| `AAK-S104` | Harden intercept wrappers for captured source provenance and identity context | `AAK-S101` |

### Acceptance Tests

1. Existing tests remain green (`pytest -q`).
2. New gate file added: `tests/acceptance/test_week2_contract_gate.py`.
3. Gate validates schema invariants and naming consistency across exported bundle and demo scripts.

## `AAK-E2` CLI Contract (Weeks 1-2)

Objective: ship a stable CLI surface for v0.1 workflows.

### Stories

| Story ID | Story | Dependencies |
|----------|-------|--------------|
| `AAK-S201` | Implement `aak capture run --config ... --out ...` | `AAK-E0` |
| `AAK-S202` | Implement `aak replay verify --bundle ...` | `AAK-S201` |
| `AAK-S203` | Implement `aak stress run --bundle ... --profile ...` | `AAK-S202` |
| `AAK-S204` | Add CLI help, usage docs, and exit code conventions | `AAK-S201` |

### Acceptance Tests

1. New gate file added: `tests/acceptance/test_week2_cli_gate.py`.
2. Commands return deterministic exit codes for success/failure.
3. `--help` for all three commands documents non-claims language.

## `AAK-E3` Replay Core (Weeks 3-4)

Objective: implement deterministic replay of captured execution events.

### Stories

| Story ID | Story | Dependencies |
|----------|-------|--------------|
| `AAK-S301` | Implement replay timeline engine (ordered envelopes + payload linkage) | `AAK-E1`, `AAK-E2` |
| `AAK-S302` | Implement replay integrity checks as reusable module and CLI binding | `AAK-S301` |
| `AAK-S303` | Add replay diff mode for repeated runs under same environment | `AAK-S301` |
| `AAK-S304` | Document deterministic replay guarantee boundaries | `AAK-S302` |

### Acceptance Tests

1. New gate file added: `tests/acceptance/test_week4_replay_gate.py`.
2. Same bundle replayed 100 times in same environment yields identical ordered timeline/hash results.
3. Tampered bundle replay fails deterministically with explicit failure reason.
4. Replay of hosted LLM output is documented as integrity replay, not output reproduction.

## `AAK-E4` Stress Runner v0.1 (Weeks 5-6)

Objective: ship one strict, deterministic stress profile (`authority`) for week-6 gate.

### Stories

| Story ID | Story | Dependencies |
|----------|-------|--------------|
| `AAK-S401` | Implement profile `authority` | `AAK-E3` |
| `AAK-S402` | Emit deterministic stress artifacts (`stress_run.json`, `stress_diff.json`) | `AAK-S401` |
| `AAK-S403` | Freeze stress diff contract (`strict-identical`) | `AAK-S402` |
| `AAK-S404` | Validate reproducibility and enforce week-6 trigger | `AAK-S402`, `AAK-S403` |
| `AAK-S405` | Defer additional profiles (`urgency`, `conflicting-instructions`) to post-gate queue | `AAK-S404` |

### Acceptance Tests

1. New gate file added: `tests/acceptance/test_week6_stress_gate.py`.
2. Authority profile run is reproducible with fixed seed/config using strict-identical artifact comparison.
3. Gate validates stress run fails closed on missing/extra/modified bundle artifacts.
4. If gate fails by week 6, backlog automation marks non-essential v0.1 work as deferred.

## `AAK-E5` Evidence and Export Ops (Weeks 7-9)

Objective: ensure operator-ready end-to-end forensic workflow.

### Stories

| Story ID | Story | Dependencies |
|----------|-------|--------------|
| `AAK-S501` | Implement one-command flow for capture -> verify -> replay -> stress -> export | `AAK-E4` |
| `AAK-S502` | Integrate templates for IR, red-team, and evidence handoff into export workflow | `AAK-S501` |
| `AAK-S503` | Add runtime and retention guidance for chain-of-custody handling | `AAK-S501` |
| `AAK-S504` | Add one framework adapter integration gate (OpenClaw demo adapter) | `AAK-S501` |

### Acceptance Tests

1. New gate file added: `tests/acceptance/test_week9_ops_gate.py`.
2. Fresh environment can complete end-to-end flow in under 60 minutes.
3. Export bundle verifies standalone with `verify.py` and includes required templates/metadata.
4. Framework adapter gate validates one scripted session emits valid AAK bundle and replay passes.

## `AAK-E6` Pilot Readiness (Weeks 10-12)

Objective: produce production-like pilot package without breaking open-core boundaries.

### Stories

| Story ID | Story | Dependencies |
|----------|-------|--------------|
| `AAK-S601` | Build pilot deployment runbook and troubleshooting matrix | `AAK-E5` |
| `AAK-S602` | Define paid-layer pilot features that do not weaken OSS truth primitives | `AAK-E5` |
| `AAK-S603` | Create measurement dashboard for v0.1 metrics | `AAK-S601` |

### Acceptance Tests

1. Pilot package includes runbook, demo case, and measurement script.
2. Open-core floor remains fully functional without paid services.
3. v0.1 KPI report covers replay time, replay fidelity, verification time, and stress reproducibility.

## Release Gate (v0.1)

v0.1 is releasable only if all of the following are true:

1. `AAK-E0` through `AAK-E5` are complete with passing gates.
2. v0.1 metric thresholds from claim contract are met.
3. Lane-boundary and open-core checks pass review.

`AAK-E6` may continue post-release, but cannot change v0.1 claim language without change-control approval.
