# AAK Decision Context Contract v0.3

Status: Active implementation contract
Scope: Optional but first-class decision-context capture for exhibit-grade lineage

## Purpose

This contract defines how AAK records what the system had available at decision time.

Decision context is evidence only.

It is used to document:

- perceived world state at the time of action
- upstream inputs and context references
- confidence signals or explicit absence of such signals
- accountability and policy metadata
- reversibility and review checkpoints

## Lane Boundary

Decision context in AAK:

- does not assign governance authority
- does not certify correctness
- does not infer intent
- does not replace legal, compliance, or board review

## Event Extension

`EventBase` may include optional `decision_context`.

`decision_context` may contain:

- `snapshot_id`
- `captured_at`
- `requested_by`
- `approved_by`
- `environment`
- `policy_version`
- `action_summary`
- `reversible`
- `perceived_world_state`
- `upstream_inputs`
- `confidence_signals`
- `missing_confidence_signals`
- `context_references`
- `counterfactual_checks`

## Content Rules

- All fields must be derived from recorded runtime inputs, declared workflow metadata, or deterministic enrichment layers.
- Confidence absence must be recordable without implying a claim of safety or correctness.
- Context references should point to bundle artifacts or deterministic IDs when possible.
- Counterfactual checks must be phrased as review prompts, not as causality claims.

## Report Rules

When decision context is present, exhibit-grade report output must render:

- accountability fields
- chronological decision context chain
- reversibility markers
- counterfactual review checklist

When decision context is absent, the output must render explicit `UNKNOWN` or `not recorded` markers.

## Non-Claims

This contract does not claim:

- that recorded context is complete
- that the system interpretation was correct
- that any decision was justified
- that the resulting evidence is authoritative by itself
