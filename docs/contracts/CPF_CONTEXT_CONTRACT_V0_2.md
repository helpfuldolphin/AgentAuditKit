# AAK CPF Context Contract v0.2

Status: Draft, implementation-target contract for optional psych linkage  
Scope: Lane B forensic evidence enrichment only

## Purpose

This contract defines how Agent Audit Kit may carry optional CPF-style psychological context in evidence artifacts.

AAK remains Lane B:
- evidence only
- non-authoritative
- non-governance

Evidence is not authority.

## Lane Boundary Rule (Hard)

Psych context fields in AAK:
- do not assign trust class
- do not produce governance verdicts
- do not replace Lane A verification routes
- do not grant compliance authority

AAK may reference Lane A artifacts by hash or ID, but AAK never interprets or upgrades them into authority claims.

## Event Payload Extension

`EventBase` may include optional `psych_context`.

Core fields:
- `source`: `captured | synthetic`
- `capture_mode`: `hash_ref | inline_minimal`
- `snapshot_id` (optional)
- `convergence_score` in `[0.0, 1.0]` (optional)
- `elevated_categories` (optional)
- `elevated_indicators` (optional, compact)
- `artifact_path` + `artifact_hash` (paired optional fields)

Default mode:
- If psych context is enabled, `hash_ref` is the default mode.

## Optional Triple-Root Cross-Links

For interoperability, psych context may include optional references:
- `psych_root_hash` (expected to reference `p_t` from Lane A contexts)
- `reasoning_root_ref` (optional)
- `ui_root_ref` (optional)

These are references only. AAK does not validate governance semantics.

## Bundle Verification Behavior

If any event declares psych artifact references:
- all declared psych artifacts must exist
- no undeclared extra psych artifacts may exist
- each artifact hash must match deterministic canonical hashing

Verification fails closed on mismatch.

## Determinism Rules

For identical bundle bytes:
- replay verification result must be identical
- deterministic report output must be byte-identical

No hosted-LLM determinism claim is implied.

## Minimal CEO-Fraud Example

Illustrative event-level sequence (for contract clarity):
- `10:30` authority cue appears -> `snapshot_id=spf_1030`, `convergence_score=0.20`
- `11:00` urgency converges -> `snapshot_id=spf_1100`, `convergence_score=0.75`
- `11:15` social proof converges -> `snapshot_id=spf_1115`, `convergence_score=0.85`
- AAK records these as evidence references only, without assigning governance authority

## Non-Claims

This contract does not claim:
- correctness of psych detection
- formal verification of psychological interpretation
- legal or compliance certification
- Lane B -> Lane A admissibility without a separate explicit admissibility contract
