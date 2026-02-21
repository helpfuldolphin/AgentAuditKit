# AAK Defensible Narrative Report v0.1.0

NON-CLAIMS: This report is a deterministic summary of recorded events from an AAK evidence bundle. It does not assert correctness, safety, compliance certification, or governance authority.

## Run Metadata
- bundle_id: run_psychceocac20260221
- created_at: 2026-02-21T22:39:53.766512Z
- event_count: 9
- chain_root: e7bbcdbe0b87783ea56fe5907fa55dffde1c5c9842efae768c88ad99ff6d930c
- chain_head: 874f11b98637c543ddc672adf3f1ba8aa39347caa00e97369bbf17846d468bce
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
- verify_message: Verified 9 events
- timeline_hash: a760a0a359adecf4e8658d47c53c75d9b7ae0dba8e872e4048663988ab923abe
- clock_policy: seq_asc_then_manifest_timestamp

## Condensed Timeline
- seq=000 | timestamp=2026-02-21T10:29:50Z | event_type=session_start | payload_file=events/000_session_start.json | event_hash=e7bbcdbe0b87783ea56fe5907fa55dffde1c5c9842efae768c88ad99ff6d930c
- seq=001 | timestamp=2026-02-21T10:30:00Z | event_type=llm_request | payload_file=events/001_llm_request.json | event_hash=00bff3810bb81688436ea1d0c614e1b95b83b3f0d4005422ef8bc6b940237c38
- seq=002 | timestamp=2026-02-21T10:30:06Z | event_type=llm_response | payload_file=events/002_llm_response.json | event_hash=70e268e12555f47933010cf9990f9d3f5ea326bf96d91c44f5a8eec427cd63f6
- seq=003 | timestamp=2026-02-21T11:00:00Z | event_type=llm_request | payload_file=events/003_llm_request.json | event_hash=c4fc03b6acd7dc8aa6c02d669df5956c942f756331967a05e0f6cfab0826ad60
- seq=004 | timestamp=2026-02-21T11:00:08Z | event_type=llm_response | payload_file=events/004_llm_response.json | event_hash=1356727d00995daabaa7a60cf419b6f12e5f684e15adc8e454dae44c62662fd7
- seq=005 | timestamp=2026-02-21T14:00:00Z | event_type=llm_request | payload_file=events/005_llm_request.json | event_hash=01e7137e25fcbcba56565ed5c04f71167a0206d4f67584aac022e03796a76e59
- seq=006 | timestamp=2026-02-21T14:00:05Z | event_type=tool_call | payload_file=events/006_tool_call.json | event_hash=8cc31cec3374e4c496ab728ab6d87df26d339a675b70c4b5206f4135541bc771
- seq=007 | timestamp=2026-02-21T14:00:06Z | event_type=tool_result | payload_file=events/007_tool_result.json | event_hash=107de94222101cfccca4bfa009b90ec47b65009a01637dfcc9cff3f5047d9019
- seq=008 | timestamp=2026-02-21T14:00:09Z | event_type=llm_response | payload_file=events/008_llm_response.json | event_hash=baa371b7635e40322c865858d32d3cda8aea0d9ab4a338699af94b4d970231a6

## Decision Points (Rule-Based)
- seq=004 | event_type=llm_response | reason=Model output requested a tool invocation | payload_file=events/004_llm_response.json | event_hash=1356727d00995daabaa7a60cf419b6f12e5f684e15adc8e454dae44c62662fd7
- seq=006 | event_type=tool_call | reason=Tool invocation crossed an execution boundary | payload_file=events/006_tool_call.json | event_hash=8cc31cec3374e4c496ab728ab6d87df26d339a675b70c4b5206f4135541bc771
- seq=007 | event_type=tool_result | reason=Tool result changed execution state | payload_file=events/007_tool_result.json | event_hash=107de94222101cfccca4bfa009b90ec47b65009a01637dfcc9cff3f5047d9019

## Psychological Context (Captured/Referenced)
- seq=001 | snapshot_id=spf_1030 | source=synthetic | capture_mode=hash_ref | convergence_score=0.2 | psych_root_hash=d1468672d21aaee7249ac37c750cdc682bc26f69431fae93e20d1c6311689ae2 | artifact_path=psych/000_spf_1030.json | artifact_hash=c2c4d8c75a6ee7dc5968e87ed0762029db4c615e4829f5ebec038b7c28663beb
- seq=002 | snapshot_id=spf_1030 | source=synthetic | capture_mode=hash_ref | convergence_score=0.2 | psych_root_hash=d1468672d21aaee7249ac37c750cdc682bc26f69431fae93e20d1c6311689ae2 | artifact_path=psych/000_spf_1030.json | artifact_hash=c2c4d8c75a6ee7dc5968e87ed0762029db4c615e4829f5ebec038b7c28663beb
- seq=003 | snapshot_id=spf_1100 | source=synthetic | capture_mode=hash_ref | convergence_score=0.75 | psych_root_hash=e1ceac80c23da73dfd81f61c0013c24d1a747ee3c4b7aa17c99dfae9961f7913 | artifact_path=psych/001_spf_1100.json | artifact_hash=342bc4731d1114cc1f990cdefaf5e0fbaa51bab7d3dd0a1dd7f444ba0005d663
- seq=004 | snapshot_id=spf_1100 | source=synthetic | capture_mode=hash_ref | convergence_score=0.75 | psych_root_hash=e1ceac80c23da73dfd81f61c0013c24d1a747ee3c4b7aa17c99dfae9961f7913 | artifact_path=psych/001_spf_1100.json | artifact_hash=342bc4731d1114cc1f990cdefaf5e0fbaa51bab7d3dd0a1dd7f444ba0005d663
- seq=005 | snapshot_id=cac_1400 | source=synthetic | capture_mode=hash_ref | convergence_score=0.4 | psych_root_hash=22b38071da6dbbbfedd12bc0d97f667ab11be522b2d20357dbeb2e1836f3b5e7 | artifact_path=psych/002_cac_1400.json | artifact_hash=f5a4e214a9526f1954f4a82284c6ab03dbdb84036c987917e5a7bb96d9638622
- seq=006 | snapshot_id=cac_1400 | source=synthetic | capture_mode=hash_ref | convergence_score=0.4 | psych_root_hash=22b38071da6dbbbfedd12bc0d97f667ab11be522b2d20357dbeb2e1836f3b5e7 | artifact_path=psych/002_cac_1400.json | artifact_hash=f5a4e214a9526f1954f4a82284c6ab03dbdb84036c987917e5a7bb96d9638622
- seq=007 | snapshot_id=cac_1400 | source=synthetic | capture_mode=hash_ref | convergence_score=0.4 | psych_root_hash=22b38071da6dbbbfedd12bc0d97f667ab11be522b2d20357dbeb2e1836f3b5e7 | artifact_path=psych/002_cac_1400.json | artifact_hash=f5a4e214a9526f1954f4a82284c6ab03dbdb84036c987917e5a7bb96d9638622
- seq=008 | snapshot_id=cac_1400 | source=synthetic | capture_mode=hash_ref | convergence_score=0.4 | psych_root_hash=22b38071da6dbbbfedd12bc0d97f667ab11be522b2d20357dbeb2e1836f3b5e7 | artifact_path=psych/002_cac_1400.json | artifact_hash=f5a4e214a9526f1954f4a82284c6ab03dbdb84036c987917e5a7bb96d9638622

## Tool Calls And Side Effects
- seq=006 | kind=tool_call | tool_name=delete_security_logs | triggered_by_seq=4 | payload_file=events/006_tool_call.json
- seq=007 | kind=tool_result | tool_name=delete_security_logs | success=false | side_effect=execution-no-op | call_seq=6 | payload_file=events/007_tool_result.json

## Explicit Non-Claims
- This report summarizes recorded events only.
- This report does not prove decision correctness or policy compliance.
- This report does not reproduce hosted-LLM outputs deterministically.
