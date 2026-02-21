# AAK Audit Report Contract v0.1

Status: Optional derived artifact for v0.1 (does not change wedge claims)  
Command surface: `aak report generate --bundle <path> --out <dir>`

## Scope

The audit report is a deterministic, regulator-readable summary generated from an existing bundle.

- Input: verified replay bundle only
- Output: `audit_report.md`
- No new capture signals
- No external services
- No LLM calls

## Determinism Rule

For the same bundle bytes:

- `audit_report.md` must be byte-identical across repeated runs
- report generator behavior is fail-closed if bundle verification fails

## Fail-Closed Rule

`aak report generate` must fail if replay verification fails due to:

- modified bundle artifact
- missing bundle artifact
- extra undeclared bundle artifact

## Required Report Sections

`audit_report.md` must include the following sections in fixed order:

1. `Run Metadata`
2. `Control And Accountability Fields`
3. `Replay Verification Summary`
4. `Condensed Timeline`
5. `Decision Points (Rule-Based)`
6. `Psychological Context (Captured/Referenced)` (may render `- none`)
7. `Tool Calls And Side Effects`
8. `Explicit Non-Claims`

## Required Content Rules

- Non-claims statement must appear near the top of the report.
- Unknown accountability fields must be explicitly rendered as `UNKNOWN`.
- Decision points must be rule-based from existing event payloads only.
- No normative claims about correctness, safety, or compliance.

## Non-Claims / Disclaimers (Mandatory)

The report is a derived rendering of bundle artifacts only.

- It is not a truth claim.
- It is not a compliance certification.
- It does not infer intent.
- It does not infer causality.
- It does not evaluate correctness of actions.
- It does not provide safety or security guarantees.

The report may describe only:

- what was recorded in the bundle
- what replay verification passed/failed
- what stress/replay artifacts matched or differed
- what fields are unknown

## Non-Claims (Mandatory)

The report is:

- a summary of recorded events
- not a correctness proof
- not a compliance certification
- not deterministic hosted-LLM output reproduction
