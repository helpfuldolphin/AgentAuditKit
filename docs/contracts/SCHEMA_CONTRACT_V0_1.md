# AAK Schema Contract v0.1

Status: Frozen for v0.1  
Applies to: Event payloads, event envelopes, replay manifest, bundle layout

## Manifest Contract

Canonical identifier field:

- `bundle_id` (required)

Required top-level fields:

- `version`
- `bundle_id`
- `created_at`
- `chain_root`
- `chain_head`
- `events`
- `event_count`
- `metadata`
- `threat_flags`
- `disclaimer`

## Event Envelope Contract

Each item in `events` must include:

- `seq`
- `event_type`
- `hash`
- `prev_hash`
- `timestamp`
- `payload_file`

## Event Payload Contract

Each payload file under `events/` is hashed as:

`event_hash = domain_hash("event", payload_json)`

Envelope fields are not included in payload hashing.

## Bundle Layout Contract

Expected exported structure:

- `replay_manifest.json`
- `events/*.json`
- `verify.py`
- `README.txt`

Optional v0.2 extension artifacts (when psych context references are present):

- `psych/**/*.json`

Verification policy:

- Fail closed on missing referenced payloads
- Fail closed on modified payload hashes
- Fail closed on extra files in `events/` not declared in manifest

If psych artifacts are referenced by event payloads:

- Fail closed on missing referenced psych artifacts
- Fail closed on modified psych artifact hashes
- Fail closed on extra files in `psych/` not referenced by event payloads

## Naming Compatibility Rule

- `bundle_id` is the canonical manifest identity field for v0.1.
- Compatibility with historical `run_id` references in scripts may be retained as fallback only.
