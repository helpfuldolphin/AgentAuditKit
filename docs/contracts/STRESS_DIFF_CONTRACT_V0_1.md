# AAK Stress Diff Contract v0.1

Status: Frozen for v0.1 week-6 gate  
Profile scope: `authority` only for the initial reproducibility gate

## Determinism Mode

For v0.1 week-6 gate, stress determinism is strict:

- Same input bundle + same profile + same seed -> identical `stress_run.json`
- Same input bundle + same profile + same seed -> identical `stress_diff.json`

No tolerance window is used in this gate.

## Artifact Files

A stress output directory must contain:

- `stress_run.json`
- `stress_diff.json`

## `stress_diff.json` Required Fields

- `version`
- `profile`
- `bundle_id`
- `determinism_mode` (`strict-identical`)
- `baseline_timeline_hash`
- `stressed_timeline_hash`
- `change_count`
- `changes`
- `diff_hash`

## `stress_run.json` Required Fields

- `version`
- `profile`
- `bundle_id`
- `seed`
- `finding_count`
- `findings`
- `baseline_timeline_hash`
- `diff_hash`
- `run_hash`
- `non_claims`

## Verification Rule

Stress run must fail closed if replay verification fails due to:

- missing bundle artifacts
- extra bundle artifacts
- modified bundle artifacts
