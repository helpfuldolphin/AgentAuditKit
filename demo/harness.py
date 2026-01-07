#!/usr/bin/env python3
"""
Demo harness: produces a bundle with >=3 tool calls and ASI-tagged threat flags.

All events are marked as SYNTHETIC for provenance discipline.

Usage:
    python demo/harness.py --output ./demo_output
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src and demo to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from mock_tools import TOOL_REGISTRY, calculate_metrics, search_kb

from aak.canon.hasher import domain_hash
from aak.models.events import (
    EventSource,
    LLMRequestEvent,
    LLMResponseEvent,
    SessionStartEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from aak.models.identity import ActorType, IdentityContext
from aak.models.threats import (
    OWASPAgenticTag,
    Severity,
    ThreatClass,
    ThreatFlag,
)
from aak.vault.export import export_bundle
from aak.vault.store import VaultWriter


def run_demo(output_path: Path) -> None:
    """Execute demo scenario and produce bundle."""
    vault_path = output_path / "vault"
    bundle_path = output_path / "bundle"

    # Initialize vault
    writer = VaultWriter(vault_path)
    threat_flags: list[ThreatFlag] = []

    # Identity context for the agent
    agent_identity = IdentityContext(
        actor_type=ActorType.AGENT,
        actor_id="demo-summarizer-agent",
        actor_name="Document Summarizer",
        roles=["assistant", "document_reader"],
        permissions=["read:documents", "compute"],
        permission_source="system_config",
    )

    print(f"[DEMO] Starting capture session: {writer.run_id}")
    print("[DEMO] All events marked as SYNTHETIC for provenance discipline")
    print()

    # Event 0: Session start
    writer.append_event(
        SessionStartEvent(
            run_id=writer.run_id,
            sdk_version="0.1.0",
            vault_path=str(vault_path),
            identity_context=agent_identity,
            source=EventSource.SYNTHETIC,
        )
    )

    # Event 1: LLM Request (user asks for Q3 summary)
    messages = [
        {
            "role": "system",
            "content": "You are a document analyst. Use search_kb to find information.",
        },
        {
            "role": "user",
            "content": "Summarize the Q3 2025 earnings from our knowledge base.",
        },
    ]
    req_event = LLMRequestEvent(
        model_id="gpt-4o-2025-01-01",
        messages=messages,
        temperature=0.0,
        provider="openai",
        tools=[{"type": "function", "function": {"name": "search_kb"}}],
        identity_context=agent_identity,
        source=EventSource.SYNTHETIC,
    )
    env1 = writer.append_event(req_event)
    print(f"[DEMO] Event {env1.seq}: LLM request")

    # Event 2: LLM Response (model calls search_kb)
    resp_event = LLMResponseEvent(
        model_id="gpt-4o-2025-01-01",
        content=None,
        tool_calls=[
            {
                "id": "call_001",
                "type": "function",
                "function": {
                    "name": "search_kb",
                    "arguments": '{"query": "Q3 earnings revenue"}',
                },
            }
        ],
        finish_reason="tool_calls",
        request_hash=env1.hash,
        input_tokens=150,
        output_tokens=25,
        identity_context=agent_identity,
        source=EventSource.SYNTHETIC,
    )
    env2 = writer.append_event(resp_event)
    print(f"[DEMO] Event {env2.seq}: LLM response (tool_calls)")

    # Event 3: Tool call - search_kb
    tool_input_1 = {"query": "Q3 earnings revenue"}
    tc_event1 = ToolCallEvent(
        tool_name="search_kb",
        tool_input=tool_input_1,
        tool_input_hash=domain_hash("tool_call", tool_input_1),
        triggered_by_seq=env2.seq,
        identity_context=agent_identity,
        source=EventSource.SYNTHETIC,
    )
    env3 = writer.append_event(tc_event1)
    print(f"[DEMO] Event {env3.seq}: Tool call search_kb")

    # Event 4: Tool result - includes poisoned chunk
    tool_output_1 = search_kb("Q3 earnings revenue")
    tr_event1 = ToolResultEvent(
        tool_name="search_kb",
        tool_output=tool_output_1,
        tool_output_hash=domain_hash("tool_result", tool_output_1),
        latency_ms=45,
        success=True,
        call_seq=env3.seq,
        identity_context=agent_identity,
        source=EventSource.SYNTHETIC,
    )
    env4 = writer.append_event(tr_event1)
    print(f"[DEMO] Event {env4.seq}: Tool result (contains poisoned chunk)")

    # Detect RAG poisoning
    for chunk in tool_output_1:
        chunk_text = chunk.get("text", "")
        if "SYSTEM:" in chunk_text or "ignore" in chunk_text.lower():
            flag = ThreatFlag(
                flag_id=f"flag_{env4.seq}_rag_poison",
                threat_class=ThreatClass.RAG_POISONING,
                severity=Severity.HIGH,
                owasp_asi_tags=[OWASPAgenticTag.ASI01, OWASPAgenticTag.ASI06],
                event_seq=env4.seq,
                evidence_hash=domain_hash("event", chunk),
                description=(
                    f"Injection pattern detected in retrieved chunk '{chunk.get('id')}': "
                    "contains 'SYSTEM:' instruction attempting to override agent behavior."
                ),
                detector_id="rag_poisoning_detector",
                detector_version="0.1.0",
                confidence=0.92,
                detected_at=datetime.now(timezone.utc),
                raw_evidence={
                    "chunk_id": chunk.get("id"),
                    "snippet": chunk_text[:200],
                },
            )
            threat_flags.append(flag)
            print(f"[DEMO] THREAT FLAG: {flag.threat_class.value} (ASI01, ASI06)")

    # Event 5: LLM Response 2 - model follows injection, calls get_employee_ssn_list
    resp_event2 = LLMResponseEvent(
        model_id="gpt-4o-2025-01-01",
        content=None,
        tool_calls=[
            {
                "id": "call_002",
                "type": "function",
                "function": {"name": "get_employee_ssn_list", "arguments": "{}"},
            }
        ],
        finish_reason="tool_calls",
        request_hash=env4.hash,
        input_tokens=300,
        output_tokens=20,
        identity_context=agent_identity,
        source=EventSource.SYNTHETIC,
    )
    env5 = writer.append_event(resp_event2)
    print(f"[DEMO] Event {env5.seq}: LLM response (malicious tool call)")

    # Event 6: Tool call - get_employee_ssn_list (TOOL MISUSE)
    tool_input_2: dict = {}
    tc_event2 = ToolCallEvent(
        tool_name="get_employee_ssn_list",
        tool_input=tool_input_2,
        tool_input_hash=domain_hash("tool_call", tool_input_2),
        triggered_by_seq=env5.seq,
        identity_context=agent_identity,
        source=EventSource.SYNTHETIC,
    )
    env6 = writer.append_event(tc_event2)
    print(f"[DEMO] Event {env6.seq}: Tool call get_employee_ssn_list (MISUSE)")

    # Detect tool misuse
    tool_config = TOOL_REGISTRY.get("get_employee_ssn_list", {})
    required_permission = tool_config.get("permission", "unknown")
    if required_permission not in agent_identity.permissions:
        flag = ThreatFlag(
            flag_id=f"flag_{env6.seq}_tool_misuse",
            threat_class=ThreatClass.TOOL_MISUSE,
            severity=Severity.CRITICAL,
            owasp_asi_tags=[OWASPAgenticTag.ASI02, OWASPAgenticTag.ASI03],
            event_seq=env6.seq,
            evidence_hash=tc_event2.tool_input_hash,
            description=(
                f"Tool 'get_employee_ssn_list' invoked without required permission "
                f"'{required_permission}'. Agent has permissions: {agent_identity.permissions}. "
                "This is a privilege escalation attempt triggered by RAG poisoning."
            ),
            detector_id="tool_misuse_detector",
            detector_version="0.1.0",
            confidence=0.98,
            detected_at=datetime.now(timezone.utc),
            raw_evidence={
                "tool_name": "get_employee_ssn_list",
                "required_permission": required_permission,
                "agent_permissions": agent_identity.permissions,
            },
        )
        threat_flags.append(flag)
        print(f"[DEMO] THREAT FLAG: {flag.threat_class.value} (ASI02, ASI03)")

    # Event 7: Tool result - blocked (simulating a guard)
    tr_event2 = ToolResultEvent(
        tool_name="get_employee_ssn_list",
        tool_output={"error": "PermissionDenied: Insufficient privileges for PII access"},
        tool_output_hash=domain_hash("tool_result", {"error": "PermissionDenied"}),
        latency_ms=2,
        success=False,
        error_message="PermissionDenied",
        call_seq=env6.seq,
        identity_context=agent_identity,
        source=EventSource.SYNTHETIC,
    )
    env7 = writer.append_event(tr_event2)
    print(f"[DEMO] Event {env7.seq}: Tool result (blocked)")

    # Event 8: Safe tool call - calculate_metrics
    tool_input_3 = {"revenue": 4.2, "profit": 0.8}
    tc_event3 = ToolCallEvent(
        tool_name="calculate_metrics",
        tool_input=tool_input_3,
        tool_input_hash=domain_hash("tool_call", tool_input_3),
        triggered_by_seq=env7.seq,
        identity_context=agent_identity,
        source=EventSource.SYNTHETIC,
    )
    env8 = writer.append_event(tc_event3)
    print(f"[DEMO] Event {env8.seq}: Tool call calculate_metrics (safe)")

    # Event 9: Tool result
    tool_output_3 = calculate_metrics(4.2, 0.8)
    tr_event3 = ToolResultEvent(
        tool_name="calculate_metrics",
        tool_output=tool_output_3,
        tool_output_hash=domain_hash("tool_result", tool_output_3),
        latency_ms=1,
        success=True,
        call_seq=env8.seq,
        identity_context=agent_identity,
        source=EventSource.SYNTHETIC,
    )
    env9 = writer.append_event(tr_event3)
    print(f"[DEMO] Event {env9.seq}: Tool result (metrics)")

    # Finalize vault
    chain_head = writer.finalize()
    print()
    print(f"[DEMO] Session finalized. Chain head: {chain_head[:16]}...")
    print(f"[DEMO] Total events: {len(writer.get_envelopes())}")
    print(f"[DEMO] Threat flags: {len(threat_flags)}")

    # Export bundle
    print()
    print(f"[DEMO] Exporting bundle to {bundle_path}")
    result = export_bundle(
        vault_path,
        bundle_path,
        include_verify_script=True,
        threat_flags=threat_flags,
    )

    print("[DEMO] Bundle created:")
    print(f"       - Events: {result.event_count}")
    print(f"       - Threat flags: {result.threat_flags_count}")
    print(f"       - Manifest hash: {result.manifest_hash[:16]}...")

    # Print summary
    print()
    print("=" * 60)
    print("DEMO SUMMARY")
    print("=" * 60)
    print(f"Bundle path: {bundle_path}")
    print("Tool calls captured: 3 (search_kb, get_employee_ssn_list, calculate_metrics)")
    print(f"Threat flags with OWASP ASI tags: {len(threat_flags)}")
    for flag in threat_flags:
        tags = ", ".join(t.value for t in flag.owasp_asi_tags)
        print(f"  - [{flag.severity.value}] {flag.threat_class.value}: {tags}")
    print()
    print("To verify bundle:")
    print(f"  cd {bundle_path} && python verify.py")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Audit Kit Demo Harness")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./demo_output"),
        help="Output directory for demo artifacts",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    run_demo(args.output)


if __name__ == "__main__":
    main()
