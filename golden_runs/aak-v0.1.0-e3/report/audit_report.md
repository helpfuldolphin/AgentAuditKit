# AAK Defensible Narrative Report v0.1.0

NON-CLAIMS: This report is a deterministic summary of recorded events from an AAK evidence bundle. It does not assert correctness, safety, compliance certification, or governance authority.

## Run Metadata
- bundle_id: run_f1ff76f49bfc60eb
- created_at: 2026-02-18T02:15:11.564263Z
- event_count: 3
- chain_root: 4fa5e8e18df364e28fe59ecfd0dcd250e4c917678f6b55198234a5af1ee2065e
- chain_head: 7a7e090eaa4349b16e7fe74578f74084d7c87c98c9cf4f8543b2336c6ba9bdb4
- sdk_version: 0.1.0
- model_id: UNKNOWN
- provider: UNKNOWN
- sampling_params: {}

## Control And Accountability Fields
- requested_by: UNKNOWN
- approved_by: UNKNOWN
- environment: UNKNOWN
- policy_version: UNKNOWN

## Replay Verification Summary
- verify_status: PASS
- verify_message: Verified 3 events
- timeline_hash: b8902fd0672d72c4bd19227d81054263badc1b9c5d6315d341beeb2539f12e91
- clock_policy: seq_asc_then_manifest_timestamp

## Condensed Timeline
- seq=000 | timestamp=2026-02-18T02:15:11.528734Z | event_type=session_start | payload_file=events/000_session_start.json | event_hash=4fa5e8e18df364e28fe59ecfd0dcd250e4c917678f6b55198234a5af1ee2065e
- seq=001 | timestamp=2026-02-18T02:15:11.529733Z | event_type=llm_request | payload_file=events/001_llm_request.json | event_hash=b48a2e4a28d429af4854bd8bbc6766b99931c566422d4c8eef8cb27f2bb1ac66
- seq=002 | timestamp=2026-02-18T02:15:11.530733Z | event_type=llm_response | payload_file=events/002_llm_response.json | event_hash=da107d7910090ef1dcaa1697e4cb9843a8e0a792c770c4efcc23928fbe30d36f

## Decision Points (Rule-Based)
- none

## Tool Calls And Side Effects
- none

## Explicit Non-Claims
- This report summarizes recorded events only.
- This report does not prove decision correctness or policy compliance.
- This report does not reproduce hosted-LLM outputs deterministically.
