# AAK Verifier Evidence Contract v0.3

Status: Active interface contract
Scope: Optional external verifier evidence for AAK bundles

## Purpose

This contract defines how AAK may carry outputs from external verifiers, including formal proof systems and proof-oriented agents.

Examples:

- Lean/Leanstral-backed formal verification
- model checking
- static analysis or theorem proving outputs

The goal is representation and fail-closed packaging, not embedded verifier execution.

## Design Inputs

This interface is intentionally aligned with proof-agent workflows where an external agent/toolchain produces proof artifacts and a separate verifier checks them.

## Bundle Surface

Bundles may include:

- `verifier_evidence` entries in the replay manifest
- optional `verifiers/**/*.json` artifact files

Each verifier evidence entry should record:

- `claim_id`
- `verifier_id`
- `verifier_kind`
- `status`
- `verified_at`
- `proof_hash` or `result_hash`
- optional `artifact_path` + `artifact_hash`
- optional `toolchain`
- optional `notes`

## Verification Rules

If verifier evidence is declared:

- all declared verifier artifacts must exist
- no undeclared extra verifier artifacts may exist
- declared artifact hashes must match

Historical bundles without verifier evidence remain valid.

## Lane Boundary

Verifier evidence in AAK:

- may be attached as supporting evidence
- may not upgrade AAK itself into a governance authority system
- may not be treated as a legal conclusion by virtue of packaging alone

## Non-Claims

This contract does not claim:

- that a verifier result is correct merely because it is present
- that formal verification covers the entire agent workflow
- that verifier evidence replaces human review
