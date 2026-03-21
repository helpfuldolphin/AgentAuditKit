# AAK Defensible Narrative Report v0.3.0

NON-CLAIMS: This report is a deterministic summary of recorded events from an AAK evidence bundle. It does not assert correctness, safety, compliance certification, or governance authority.

## Run Metadata
- bundle_id: run_36739dd5b370869b
- created_at: 2026-03-20T14:00:00Z
- event_count: 11
- chain_root: 319f9cad86ac07861824bf997b0020349ec86a8e9fc6cfe64c89c91e516d4a70
- chain_head: 8c0bf126b4a413abe650713b0aa168021ff054bd9ab3a5244f3a86a7891cdc4b
- sdk_version: 0.3.0
- model_id: gpt-4o-2026-03-01
- provider: openai
- workflow_id: wire_review_demo
- workflow_name: Banking Decision Exposure Review
- sampling_params: {"temperature":0.0}

## Control And Accountability Fields
- requested_by: treasury_ops_queue
- approved_by: dual_control_officer
- environment: banking-prod-sim
- policy_version: wire_policy_v3

## Replay Verification Summary
- verify_status: PASS
- verify_message: Verified 11 events
- timeline_hash: 8a46fa44fb8b6516b7f287cb72b2c29ae10c1a6525cfb7bbe9a501934420bd95
- clock_policy: seq_asc_then_manifest_timestamp

## Temporal Narrative Summary
- 2026-03-20T14:00:00Z: The capture session started. Recorded action summary: not recorded. Evidence: events/000_session_start.json.
- 2026-03-20T14:00:02Z: The agent received a new decision input. Message summary: You review high-value vendor payment requests and document review actions. / Review payment PAY-2026-0319-771 before release. Record risk factors and request any needed c.... Recorded action summary: Review high-value vendor wire release request. Recorded world state: Payment amount exceeds standard auto-release threshold.; Vendor beneficiary account changed within the last 24 hours.. Missing confidence signals: out_of_band_vendor_confirmation. Reversibility: true. Evidence: events/001_llm_request.json.
- 2026-03-20T14:00:03Z: The model requested tool `lookup_vendor_profile`. Recorded action summary: Review high-value vendor wire release request. Recorded world state: Payment amount exceeds standard auto-release threshold.; Vendor beneficiary account changed within the last 24 hours.. Missing confidence signals: out_of_band_vendor_confirmation. Reversibility: true. Evidence: events/002_llm_response.json.
- 2026-03-20T14:00:05Z: The workflow crossed an execution boundary through tool `lookup_vendor_profile`. Recorded action summary: Inspect vendor profile and beneficiary change details. Recorded world state: Vendor profile lookup is pending.; No secondary approval has been recorded yet.. Missing confidence signals: secondary_approval_record. Reversibility: true. Evidence: events/003_tool_call.json.
- 2026-03-20T14:00:06Z: Tool `lookup_vendor_profile` returned a successful result. Recorded action summary: Inspect vendor profile and beneficiary change details. Recorded world state: Vendor profile lookup is pending.; No secondary approval has been recorded yet.. Missing confidence signals: secondary_approval_record. Reversibility: true. Evidence: events/004_tool_result.json.
- 2026-03-20T14:00:08Z: The agent received a new decision input. Message summary: Use policy controls before any release recommendation. / {"amount_usd": 245000, "beneficiary_account_changed_within_days": 1, "beneficiary_change_tick.... Recorded action summary: Evaluate release controls against recorded risk factors. Recorded world state: Vendor profile shows a recent beneficiary-account change.; No dual approval is present for the release request.. Missing confidence signals: dual_approval_record; out_of_band_vendor_confirmation. Reversibility: true. Evidence: events/005_llm_request.json.
- 2026-03-20T14:00:09Z: The model requested tool `check_policy_controls`. Recorded action summary: Evaluate release controls against recorded risk factors. Recorded world state: Vendor profile shows a recent beneficiary-account change.; No dual approval is present for the release request.. Missing confidence signals: dual_approval_record; out_of_band_vendor_confirmation. Reversibility: true. Evidence: events/006_llm_response.json.
- 2026-03-20T14:00:10Z: The workflow crossed an execution boundary through tool `check_policy_controls`. Recorded action summary: Evaluate release controls against recorded risk factors. Recorded world state: Vendor profile shows a recent beneficiary-account change.; No dual approval is present for the release request.. Missing confidence signals: dual_approval_record; out_of_band_vendor_confirmation. Reversibility: true. Evidence: events/007_tool_call.json.
- 2026-03-20T14:00:11Z: Tool `check_policy_controls` returned a successful result. Recorded action summary: Evaluate release controls against recorded risk factors. Recorded world state: Vendor profile shows a recent beneficiary-account change.; No dual approval is present for the release request.. Missing confidence signals: dual_approval_record; out_of_band_vendor_confirmation. Reversibility: true. Evidence: events/008_tool_result.json.
- 2026-03-20T14:00:13Z: The agent received a new decision input. Message summary: Return a final release recommendation for the queue operator. / {"amount_usd": 245000, "bank_account_age_days": 1, "dual_approval_present": false, "recommend.... Recorded action summary: Issue hold/review recommendation before funds movement. Recorded world state: Policy controls recommend hold_for_review.; Release can still be paused before any funds movement.. Missing confidence signals: out_of_band_vendor_confirmation. Reversibility: true. Evidence: events/009_llm_request.json.
- 2026-03-20T14:00:14Z: The agent produced a recorded response. Response summary: Recommendation: hold release and require dual approval plus out-of-band vendor confirmation b.... Recorded action summary: Issue hold/review recommendation before funds movement. Recorded world state: Policy controls recommend hold_for_review.; Release can still be paused before any funds movement.. Missing confidence signals: out_of_band_vendor_confirmation. Reversibility: true. Evidence: events/010_llm_response.json.

## Condensed Timeline
- seq=000 | timestamp=2026-03-20T14:00:00Z | event_type=session_start | payload_file=events/000_session_start.json | event_hash=319f9cad86ac07861824bf997b0020349ec86a8e9fc6cfe64c89c91e516d4a70
- seq=001 | timestamp=2026-03-20T14:00:02Z | event_type=llm_request | payload_file=events/001_llm_request.json | event_hash=4bb897f5bdfa188b95a70fc2b62c24af482af3a686eb70062ab37f46d831f27f
- seq=002 | timestamp=2026-03-20T14:00:03Z | event_type=llm_response | payload_file=events/002_llm_response.json | event_hash=81cdd5262b725a0bcc2a51191afabaa97b7dbccac2e129144103617fcf92611e
- seq=003 | timestamp=2026-03-20T14:00:05Z | event_type=tool_call | payload_file=events/003_tool_call.json | event_hash=2826d12778304b57b5891695d4d4b152e0ac7c6888c781df8ff20d4196b3dfd0
- seq=004 | timestamp=2026-03-20T14:00:06Z | event_type=tool_result | payload_file=events/004_tool_result.json | event_hash=ec3646e250999bd02dc35713a41d141e74184b358edfc8a3b1f133e860b0729d
- seq=005 | timestamp=2026-03-20T14:00:08Z | event_type=llm_request | payload_file=events/005_llm_request.json | event_hash=169a3b287cca56af57af4e0c526db397455b56f520f9f74abef1af2127c25dd8
- seq=006 | timestamp=2026-03-20T14:00:09Z | event_type=llm_response | payload_file=events/006_llm_response.json | event_hash=5cc8049796f52b49774a5870b6980dca4bf733efe70d576e3373d5a1d37433ae
- seq=007 | timestamp=2026-03-20T14:00:10Z | event_type=tool_call | payload_file=events/007_tool_call.json | event_hash=59ec357e1dc6f1350a2a527096bfece4f2e2ab11e2e0cae02868fe5a2fffedb8
- seq=008 | timestamp=2026-03-20T14:00:11Z | event_type=tool_result | payload_file=events/008_tool_result.json | event_hash=fcc6a2b9e80dfbbe12708c6a452244df6c1f23ffea95e70c16f78aae1f6089d0
- seq=009 | timestamp=2026-03-20T14:00:13Z | event_type=llm_request | payload_file=events/009_llm_request.json | event_hash=1cde8805fcb7548619b1e5a111a037ea1d98b785c73bdab87f46c7e67cc4175f
- seq=010 | timestamp=2026-03-20T14:00:14Z | event_type=llm_response | payload_file=events/010_llm_response.json | event_hash=b0b5f615a651ae76e78a0be0ddb5f815b5634a14a3401733897c7f3a7e182e1e

## Decision Points (Rule-Based)
- seq=002 | event_type=llm_response | reason=Model output requested a tool invocation | action_summary=Review high-value vendor wire release request | reversible=true | payload_file=events/002_llm_response.json | event_hash=81cdd5262b725a0bcc2a51191afabaa97b7dbccac2e129144103617fcf92611e
- seq=003 | event_type=tool_call | reason=Tool invocation crossed an execution boundary | action_summary=Inspect vendor profile and beneficiary change details | reversible=true | payload_file=events/003_tool_call.json | event_hash=2826d12778304b57b5891695d4d4b152e0ac7c6888c781df8ff20d4196b3dfd0
- seq=004 | event_type=tool_result | reason=Tool result changed execution state | action_summary=Inspect vendor profile and beneficiary change details | reversible=true | payload_file=events/004_tool_result.json | event_hash=ec3646e250999bd02dc35713a41d141e74184b358edfc8a3b1f133e860b0729d
- seq=006 | event_type=llm_response | reason=Model output requested a tool invocation | action_summary=Evaluate release controls against recorded risk factors | reversible=true | payload_file=events/006_llm_response.json | event_hash=5cc8049796f52b49774a5870b6980dca4bf733efe70d576e3373d5a1d37433ae
- seq=007 | event_type=tool_call | reason=Tool invocation crossed an execution boundary | action_summary=Evaluate release controls against recorded risk factors | reversible=true | payload_file=events/007_tool_call.json | event_hash=59ec357e1dc6f1350a2a527096bfece4f2e2ab11e2e0cae02868fe5a2fffedb8
- seq=008 | event_type=tool_result | reason=Tool result changed execution state | action_summary=Evaluate release controls against recorded risk factors | reversible=true | payload_file=events/008_tool_result.json | event_hash=fcc6a2b9e80dfbbe12708c6a452244df6c1f23ffea95e70c16f78aae1f6089d0

## Decision Context Chain
- seq=001 | snapshot_id=wire_review_intake | action_summary=Review high-value vendor wire release request | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=out_of_band_vendor_confirmation | context_refs=2 | payload_file=events/001_llm_request.json
- seq=002 | snapshot_id=wire_review_intake | action_summary=Review high-value vendor wire release request | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=out_of_band_vendor_confirmation | context_refs=2 | payload_file=events/002_llm_response.json
- seq=003 | snapshot_id=wire_review_vendor_lookup | action_summary=Inspect vendor profile and beneficiary change details | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=secondary_approval_record | context_refs=2 | payload_file=events/003_tool_call.json
- seq=004 | snapshot_id=wire_review_vendor_lookup | action_summary=Inspect vendor profile and beneficiary change details | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=secondary_approval_record | context_refs=2 | payload_file=events/004_tool_result.json
- seq=005 | snapshot_id=wire_review_policy_check | action_summary=Evaluate release controls against recorded risk factors | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=dual_approval_record; out_of_band_vendor_confirmation | context_refs=2 | payload_file=events/005_llm_request.json
- seq=006 | snapshot_id=wire_review_policy_check | action_summary=Evaluate release controls against recorded risk factors | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=dual_approval_record; out_of_band_vendor_confirmation | context_refs=2 | payload_file=events/006_llm_response.json
- seq=007 | snapshot_id=wire_review_policy_check | action_summary=Evaluate release controls against recorded risk factors | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=dual_approval_record; out_of_band_vendor_confirmation | context_refs=2 | payload_file=events/007_tool_call.json
- seq=008 | snapshot_id=wire_review_policy_check | action_summary=Evaluate release controls against recorded risk factors | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=dual_approval_record; out_of_band_vendor_confirmation | context_refs=2 | payload_file=events/008_tool_result.json
- seq=009 | snapshot_id=wire_review_outcome | action_summary=Issue hold/review recommendation before funds movement | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=out_of_band_vendor_confirmation | context_refs=2 | payload_file=events/009_llm_request.json
- seq=010 | snapshot_id=wire_review_outcome | action_summary=Issue hold/review recommendation before funds movement | requested_by=treasury_ops_queue | approved_by=dual_control_officer | policy_version=wire_policy_v3 | reversible=true | missing_confidence_signals=out_of_band_vendor_confirmation | context_refs=2 | payload_file=events/010_llm_response.json

## Psychological Context (Captured/Referenced)
- none

## External Verifier Evidence
- none

## Tool Calls And Side Effects
- seq=003 | kind=tool_call | tool_name=lookup_vendor_profile | triggered_by_seq=2 | reversible=true | payload_file=events/003_tool_call.json
- seq=004 | kind=tool_result | tool_name=lookup_vendor_profile | success=true | side_effect=external-change-candidate | reversible=true | call_seq=3 | payload_file=events/004_tool_result.json
- seq=007 | kind=tool_call | tool_name=check_policy_controls | triggered_by_seq=6 | reversible=true | payload_file=events/007_tool_call.json
- seq=008 | kind=tool_result | tool_name=check_policy_controls | success=true | side_effect=external-change-candidate | reversible=true | call_seq=7 | payload_file=events/008_tool_result.json

## Counterfactual Review Checklist
- seq=001 | review_check=Confirm whether an independent vendor callback occurred before release.
- seq=001 | review_check=Confirm whether a second approver should have been present at intake.
- seq=001 | review_check=Confirm whether missing confidence signal `out_of_band_vendor_confirmation` should have triggered additional review before action.
- seq=002 | review_check=Confirm whether an independent vendor callback occurred before release.
- seq=002 | review_check=Confirm whether a second approver should have been present at intake.
- seq=002 | review_check=Confirm whether missing confidence signal `out_of_band_vendor_confirmation` should have triggered additional review before action.
- seq=003 | review_check=Check whether the beneficiary change ticket was independently validated.
- seq=003 | review_check=Confirm whether missing confidence signal `secondary_approval_record` should have triggered additional review before action.
- seq=004 | review_check=Check whether the beneficiary change ticket was independently validated.
- seq=004 | review_check=Confirm whether missing confidence signal `secondary_approval_record` should have triggered additional review before action.
- seq=005 | review_check=Check whether policy required an automatic hold on recent beneficiary changes.
- seq=005 | review_check=Confirm whether missing confidence signal `dual_approval_record` should have triggered additional review before action.
- seq=005 | review_check=Confirm whether missing confidence signal `out_of_band_vendor_confirmation` should have triggered additional review before action.
- seq=006 | review_check=Check whether policy required an automatic hold on recent beneficiary changes.
- seq=006 | review_check=Confirm whether missing confidence signal `dual_approval_record` should have triggered additional review before action.
- seq=006 | review_check=Confirm whether missing confidence signal `out_of_band_vendor_confirmation` should have triggered additional review before action.
- seq=007 | review_check=Check whether policy required an automatic hold on recent beneficiary changes.
- seq=007 | review_check=Confirm whether missing confidence signal `dual_approval_record` should have triggered additional review before action.
- seq=007 | review_check=Confirm whether missing confidence signal `out_of_band_vendor_confirmation` should have triggered additional review before action.
- seq=008 | review_check=Check whether policy required an automatic hold on recent beneficiary changes.
- seq=008 | review_check=Confirm whether missing confidence signal `dual_approval_record` should have triggered additional review before action.
- seq=008 | review_check=Confirm whether missing confidence signal `out_of_band_vendor_confirmation` should have triggered additional review before action.
- seq=009 | review_check=Check whether the release would remain paused until confirmation and approval are present.
- seq=009 | review_check=Confirm whether missing confidence signal `out_of_band_vendor_confirmation` should have triggered additional review before action.
- seq=010 | review_check=Check whether the release would remain paused until confirmation and approval are present.
- seq=010 | review_check=Confirm whether missing confidence signal `out_of_band_vendor_confirmation` should have triggered additional review before action.

## Explicit Non-Claims
- This report summarizes recorded events only.
- This report does not prove decision correctness or policy compliance.
- This report does not reproduce hosted-LLM outputs deterministically.
