# AAK v0.3 Backlog

Status: Active implementation backlog
Source of truth: v0.3 exhibit-grade lineage release
Scope: decision-context capture, exhibit-grade evidence packs, verifier-evidence interface, banking pilot workflow

## Release Theme

AAK v0.3 treats agent traces as exhibit-grade evidence for post-mortem review.

Core release statement:

**AAK v0.3 captures decision lineage as replayable evidence bundles with explicit decision context, accountability metadata, regulator-readable narrative artifacts, and optional external verifier evidence.**

## Explicitly Out Of Scope

- Dashboards
- Additional stress profiles
- OpenClaw adapter implementation
- Full Leanstral integration
- Governance authority or compliance certification claims

## Sequencing

| Epic | Priority | Objective | Exit Gate |
|------|----------|-----------|-----------|
| `AAK-V3-E0` | P0 | Version hygiene and contract freeze | v0.3 naming/version surfaces coherent |
| `AAK-V3-E1` | P1 | Decision-context capture and accountability metadata | decision context flows through event capture and report generation |
| `AAK-V3-E2` | P1 | Exhibit-grade evidence pack output | evidence pack includes narrative, decision chain, counterfactual checklist, Mermaid timeline, technical bundle |
| `AAK-V3-E3` | P2 | External verifier evidence interface | optional verifier evidence can be represented and exported fail-closed |
| `AAK-V3-E4` | P1 | Banking pilot workflow | one realistic workflow generates a lighthouse evidence pack |
| `AAK-V3-E5` | P0 | Release packaging | clean `v0.3.0` release candidate ready |

## Epic Backlog

## `AAK-V3-E0` Version Hygiene And Contract Freeze

Objective: eliminate version ambiguity before shipping v0.3 outward.

### Stories

| Story ID | Story |
|----------|-------|
| `AAK-V3-S001` | Update package, CLI, report, stress, and manifest surfaces to `0.3.0` |
| `AAK-V3-S002` | Align README, changelog, release docs, and current golden artifacts with `0.3.0` story |
| `AAK-V3-S003` | Add v0.3 contracts for decision context, evidence packs, and verifier evidence |

### Acceptance Tests

1. `pyproject.toml` and `src/aak/__init__.py` report `0.3.0`.
2. No current v0.3 artifact or generated report claims a different AAK version.
3. v0.3 docs clearly distinguish historical releases from current release intent.

## `AAK-V3-E1` Decision Context And Accountability

Objective: record what the system had available at decision time.

### Stories

| Story ID | Story |
|----------|-------|
| `AAK-V3-S101` | Add `DecisionContextSnapshot` model with perceived world state, upstream inputs, confidence signals, context refs, reversibility, and counterfactual checks |
| `AAK-V3-S102` | Add accountable metadata fields (`requested_by`, `approved_by`, `environment`, `policy_version`) to capture/session metadata |
| `AAK-V3-S103` | Add optional decision-context provider plumbing to live intercept surfaces |
| `AAK-V3-S104` | Remove hardcoded `UNKNOWN` accountability handling in report generation and derive values from bundle metadata/decision context |

### Acceptance Tests

1. Events may carry `decision_context`.
2. Verified bundles round-trip decision-context content without hash drift.
3. `audit_report.md` renders recorded accountability fields when present.
4. Missing accountability data still renders explicitly as `UNKNOWN`.

## `AAK-V3-E2` Exhibit-Grade Evidence Pack

Objective: move from engineering trace output to exhibit-grade evidence pack output.

### Stories

| Story ID | Story |
|----------|-------|
| `AAK-V3-S201` | Upgrade `report generate` to emit an evidence pack directory, not just a single markdown file |
| `AAK-V3-S202` | Generate deterministic temporal narrative summary in plain language |
| `AAK-V3-S203` | Generate decision-context chain artifact and Mermaid timeline |
| `AAK-V3-S204` | Generate counterfactual review checklist readable by non-technical reviewers |
| `AAK-V3-S205` | Include the technical bundle inside the evidence pack with a manifest of derived artifacts |

### Acceptance Tests

1. Evidence pack includes `audit_report.md`, temporal narrative, counterfactual checklist, decision-context chain, Mermaid timeline, and underlying bundle copy.
2. Evidence-pack generation fails closed if replay verification fails.
3. For identical bundle bytes, evidence-pack outputs are byte-identical.

## `AAK-V3-E3` External Verifier Evidence Interface

Objective: let AAK carry formal-verification evidence without embedding verifier-specific logic.

### Stories

| Story ID | Story |
|----------|-------|
| `AAK-V3-S301` | Define verifier-evidence contract and model surfaces |
| `AAK-V3-S302` | Add export/copy/verify support for declared verifier artifacts under `verifiers/` |
| `AAK-V3-S303` | Add interface module for external prover integrations (e.g. Leanstral-backed MathLedger FV route) |

### Acceptance Tests

1. Bundles can optionally declare verifier evidence without breaking historical bundle verification.
2. Declared verifier artifacts fail closed on missing/extra/modified files.
3. Evidence pack renders verifier evidence as referenced supporting evidence, not authority upgrade.

## `AAK-V3-E4` Banking Pilot Workflow

Objective: produce one realistic enterprise-facing lighthouse workflow.

### Stories

| Story ID | Story |
|----------|-------|
| `AAK-V3-S401` | Replace scaffolded `capture run` path with a real scenario-driven capture flow |
| `AAK-V3-S402` | Add a banking decision-exposure workflow using the OpenAI interception surface |
| `AAK-V3-S403` | Capture decision context across request, tool, and outcome boundaries |
| `AAK-V3-S404` | Generate a reusable evidence pack for the pilot workflow |

### Acceptance Tests

1. `aak capture run --config ... --out ...` produces a real multi-event banking workflow bundle.
2. Resulting bundle passes replay verify, stress, and evidence-pack generation.
3. Pilot artifacts are suitable for a lighthouse demo and outreach follow-up.

## `AAK-V3-E5` Release Packaging

Objective: cut a clean `v0.3.0` release candidate.

### Stories

| Story ID | Story |
|----------|-------|
| `AAK-V3-S501` | Regenerate or add v0.3 golden artifacts and docs |
| `AAK-V3-S502` | Update release notes/outreach materials to lead with decision lineage and evidence packs |
| `AAK-V3-S503` | Prepare release tag and verification steps for `v0.3.0` |

### Acceptance Tests

1. Release notes describe exhibit-grade lineage, not psych-first framing.
2. Latest demo/release assets verify on a fresh run.
3. Versioned artifacts and docs align on `v0.3.0`.
