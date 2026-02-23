# AAK Psych Scoring Provenance Contract v0.1

Status: Draft for implementation  
Scope: Optional psych-context scoring provenance for Lane B evidence artifacts

## Purpose

This contract defines the minimum provenance fields required to make psych-context
scores explainable and auditable in AAK evidence bundles.

AAK remains evidence-only and non-authoritative.

## Required Artifact

If any event includes `psych_context`, the bundle must include:

- `psych/scoring_manifest.json`

## Required Fields (`psych/scoring_manifest.json`)

- `version`
- `taxonomy_source` (e.g., CPF taxonomy reference)
- `taxonomy_version`
- `classifier_id`
- `classifier_version`
- `score_method_id`
- `threshold_profile_id`
- `generated_at`
- `feature_schema_version`
- `features_used` (list)
- `labels_supported` (list)
- `model_card_ref` (path or ID)
- `determinism_mode` (`strict-identical` or `bounded-deterministic`)

## Per-Snapshot Provenance Requirements

For each psych snapshot referenced by `artifact_path`:

- `snapshot_id`
- `snapshot_hash`
- `classifier_id`
- `classifier_version`
- `score_method_id`
- `feature_contributions` (map of feature -> contribution)
- `score_components` (map of component -> value)
- `final_scores` (map of label -> score)
- `thresholds_applied` (map of label -> threshold)

## Verification Rules (Fail-Closed)

If psych context is present, verification must fail if:

- `psych/scoring_manifest.json` is missing
- required fields are missing
- any referenced snapshot lacks required provenance fields
- snapshot hash mismatch exists
- undeclared extra files exist under `psych/`

## Determinism Rules

For identical bundle bytes:

- replay verification result must be identical
- psych scoring provenance files must be byte-identical
- report output must be byte-identical

## Non-Claims

This contract does not claim:

- correctness of psych interpretation
- compliance certification
- legal admissibility by itself
- governance authority assignment
