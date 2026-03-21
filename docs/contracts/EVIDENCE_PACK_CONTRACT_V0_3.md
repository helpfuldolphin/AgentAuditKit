# AAK Evidence Pack Contract v0.3

Status: Active implementation contract
Command surface: `aak report generate --bundle <path> --out <dir>`

## Purpose

The evidence pack is the exhibit-grade rendering of a verified AAK bundle.

It is designed for:

- incident review
- regulator-readable chronology
- board/compliance briefing support
- legal and insurer handoff

It remains evidence-only.

## Required Outputs

For a verified bundle, the evidence pack directory must include:

- `audit_report.md`
- `temporal_narrative.md`
- `counterfactual_checklist.md`
- `decision_context_chain.json`
- `decision_timeline.mmd`
- `evidence_pack_manifest.json`
- `bundle/` copy of the technical bundle

## Determinism Rule

For identical input bundle bytes:

- all derived text artifacts must be byte-identical
- `decision_context_chain.json` must be byte-identical
- `decision_timeline.mmd` must be byte-identical
- `evidence_pack_manifest.json` must be byte-identical

## Fail-Closed Rule

Evidence-pack generation must fail if bundle verification fails due to:

- modified bundle artifact
- missing declared artifact
- extra undeclared artifact

## Narrative Rules

The temporal narrative must:

- be chronological
- use plain language
- reference technical evidence without embedding full payloads
- avoid correctness, safety, compliance, intent, or causality claims

## Counterfactual Rules

The counterfactual checklist must:

- present review prompts, not verdicts
- remain understandable to non-technical reviewers
- point back to recorded evidence or explicit missing evidence

## Non-Claims

The evidence pack is:

- a deterministic rendering of recorded evidence
- not a legal conclusion
- not a governance-grade authority artifact
- not deterministic hosted-LLM output reproduction
