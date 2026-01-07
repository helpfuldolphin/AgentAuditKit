#!/usr/bin/env python3
"""
Real capture demo: generates a run with >=3 tool calls, exports bundle, verify passes.

This demo shows CAPTURED events (not synthetic) with a real or mocked OpenAI client.

Usage:
    # With real OpenAI (requires OPENAI_API_KEY):
    python examples/real_capture_demo.py --output ./real_output

    # With mock OpenAI (for CI/testing):
    python examples/real_capture_demo.py --output ./real_output --mock

Verification:
    cd real_output/bundle && python verify.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aak.canon.hasher import domain_hash
from aak.intercept.openai_client import ToolRouter
from aak.models.events import EventSource
from aak.models.identity import ActorType, IdentityContext
from aak.models.threats import OWASPAgenticTag, Severity, ThreatClass, ThreatFlag
from aak.vault.export import export_bundle
from aak.vault.store import VaultWriter

# === Mock OpenAI for CI/testing ===


@dataclass
class MockMessage:
    content: str | None
    tool_calls: list[Any] | None = None


@dataclass
class MockChoice:
    message: MockMessage
    finish_reason: str


@dataclass
class MockUsage:
    prompt_tokens: int
    completion_tokens: int


@dataclass
class MockCompletion:
    id: str
    model: str
    choices: list[MockChoice]
    usage: MockUsage


class MockToolCall:
    def __init__(self, id: str, name: str, arguments: str):
        self.id = id
        self.type = "function"
        self.function = type("Function", (), {"name": name, "arguments": arguments})()


class MockOpenAI:
    """Mock OpenAI client for testing without API access."""

    def __init__(self) -> None:
        self.chat = self._ChatNamespace(self)
        self._call_count = 0
        self._tool_results: dict[str, Any] = {}

    def set_tool_result(self, tool_name: str, result: Any) -> None:
        """Set the result that should be returned after a tool call."""
        self._tool_results[tool_name] = result

    class _ChatNamespace:
        def __init__(self, client: "MockOpenAI"):
            self._client = client
            self.completions = self._CompletionsNamespace(client)

        class _CompletionsNamespace:
            def __init__(self, client: "MockOpenAI"):
                self._client = client

            def create(self, **kwargs: Any) -> MockCompletion:
                self._client._call_count += 1
                call_num = self._client._call_count

                # Use call count for deterministic behavior:
                # Call 1: request weather tool
                # Call 2: request stock tool
                # Call 3: request news tool
                # Call 4+: final response

                if call_num == 1:
                    # First call: request weather tool
                    return MockCompletion(
                        id=f"mock-{call_num}",
                        model=kwargs.get("model", "gpt-4"),
                        choices=[
                            MockChoice(
                                message=MockMessage(
                                    content=None,
                                    tool_calls=[
                                        MockToolCall(
                                            "call_1",
                                            "get_weather",
                                            '{"location": "San Francisco"}',
                                        )
                                    ],
                                ),
                                finish_reason="tool_calls",
                            )
                        ],
                        usage=MockUsage(prompt_tokens=50, completion_tokens=20),
                    )
                elif call_num == 2:
                    # Second call: request stock tool
                    return MockCompletion(
                        id=f"mock-{call_num}",
                        model=kwargs.get("model", "gpt-4"),
                        choices=[
                            MockChoice(
                                message=MockMessage(
                                    content=None,
                                    tool_calls=[
                                        MockToolCall(
                                            "call_2",
                                            "get_stock_price",
                                            '{"symbol": "AAPL"}',
                                        )
                                    ],
                                ),
                                finish_reason="tool_calls",
                            )
                        ],
                        usage=MockUsage(prompt_tokens=80, completion_tokens=25),
                    )
                elif call_num == 3:
                    # Third call: request news tool
                    return MockCompletion(
                        id=f"mock-{call_num}",
                        model=kwargs.get("model", "gpt-4"),
                        choices=[
                            MockChoice(
                                message=MockMessage(
                                    content=None,
                                    tool_calls=[
                                        MockToolCall(
                                            "call_3",
                                            "search_news",
                                            '{"query": "AAPL earnings"}',
                                        )
                                    ],
                                ),
                                finish_reason="tool_calls",
                            )
                        ],
                        usage=MockUsage(prompt_tokens=120, completion_tokens=30),
                    )
                else:
                    # Final response
                    return MockCompletion(
                        id=f"mock-{self._client._call_count}",
                        model=kwargs.get("model", "gpt-4"),
                        choices=[
                            MockChoice(
                                message=MockMessage(
                                    content=(
                                        "Based on my analysis: The weather in SF is sunny, "
                                        "AAPL stock is at $185.50, and recent news shows "
                                        "strong earnings."
                                    ),
                                    tool_calls=None,
                                ),
                                finish_reason="stop",
                            )
                        ],
                        usage=MockUsage(prompt_tokens=150, completion_tokens=50),
                    )


# === Tools ===


def get_weather(location: str) -> dict[str, Any]:
    """Get current weather for a location."""
    return {
        "location": location,
        "temperature": 72,
        "conditions": "sunny",
        "humidity": 45,
    }


def get_stock_price(symbol: str) -> dict[str, Any]:
    """Get current stock price."""
    return {
        "symbol": symbol,
        "price": 185.50,
        "change": 2.30,
        "change_percent": 1.26,
    }


def search_news(query: str) -> dict[str, Any]:
    """Search recent news articles."""
    return {
        "query": query,
        "results": [
            {"title": "AAPL Q4 Earnings Beat Expectations", "source": "Reuters"},
            {"title": "Apple Announces New Product Line", "source": "Bloomberg"},
        ],
    }


# === Threat Detection ===


def detect_threats(vault_path: Path) -> list[ThreatFlag]:
    """
    Run threat detection on captured events.

    For this demo, we simulate finding a low-severity flag
    when certain patterns are detected.
    """
    flags: list[ThreatFlag] = []

    # Check for potential over-reliance on external data
    events_dir = vault_path / "events"
    tool_call_count = len(list(events_dir.glob("*tool_call*.json")))

    if tool_call_count >= 3:
        # Flag for excessive agency (many tool calls)
        flags.append(
            ThreatFlag(
                flag_id="flag_excessive_agency_001",
                threat_class=ThreatClass.PRIVILEGE_MISUSE,
                severity=Severity.LOW,
                owasp_asi_tags=[OWASPAgenticTag.ASI03, OWASPAgenticTag.ASI04],
                event_seq=0,  # Session level
                evidence_hash=domain_hash("event", {"tool_call_count": tool_call_count}),
                description=(
                    f"Agent made {tool_call_count} tool calls in a single session. "
                    "Review for potential excessive agency or over-reliance on external data."
                ),
                detector_id="excessive_agency_detector",
                detector_version="0.1.0",
                confidence=0.65,
                detected_at=datetime.now(timezone.utc),
                raw_evidence={"tool_call_count": tool_call_count},
            )
        )

    return flags


# === Main Demo ===


def run_demo(output_path: Path, use_mock: bool = True) -> None:
    """Run the real capture demo."""
    vault_path = output_path / "vault"
    bundle_path = output_path / "bundle"

    # Initialize vault
    vault = VaultWriter(vault_path)

    # Identity context (CAPTURED, not synthetic)
    identity = IdentityContext(
        actor_type=ActorType.AGENT,
        actor_id="financial-assistant-agent",
        actor_name="Financial Assistant",
        roles=["assistant", "data_reader"],
        permissions=["read:weather", "read:stocks", "read:news"],
        permission_source="api_config",
    )

    print(f"[DEMO] Starting CAPTURED session: {vault.run_id}")
    print(f"[DEMO] Using {'mock' if use_mock else 'real'} OpenAI client")
    print()

    # Create OpenAI client
    if use_mock:
        client = MockOpenAI()
    else:
        try:
            from openai import OpenAI

            client = OpenAI()
        except ImportError:
            print("[ERROR] openai package not installed. Use --mock flag or install openai.")
            sys.exit(1)

    # Create tool router
    router = ToolRouter(vault, identity_context=identity, source=EventSource.CAPTURED)
    router.register("get_weather", get_weather)
    router.register("get_stock_price", get_stock_price)
    router.register("search_news", search_news)

    # Define tools for OpenAI
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_stock_price",
                "description": "Get current stock price",
                "parameters": {
                    "type": "object",
                    "properties": {"symbol": {"type": "string"}},
                    "required": ["symbol"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_news",
                "description": "Search recent news articles",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        },
    ]

    # Initial messages
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a financial assistant. "
                "Use the available tools to gather information."
            ),
        },
        {
            "role": "user",
            "content": "What's the weather in San Francisco, the current AAPL stock price, "
            "and any recent news about AAPL earnings?",
        },
    ]

    # Manually record events since we're using a mock/direct approach
    from aak.models.events import LLMRequestEvent, LLMResponseEvent

    # Conversation loop
    tool_call_count = 0
    max_iterations = 10

    for iteration in range(max_iterations):
        # Record request
        request_event = LLMRequestEvent(
            model_id="gpt-4",
            messages=messages.copy(),
            temperature=0.0,
            provider="openai",
            tools=tools,
            identity_context=identity,
            source=EventSource.CAPTURED,
        )
        req_envelope = vault.append_event(request_event)
        print(f"[DEMO] Event {req_envelope.seq}: LLM request")

        # Make API call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=tools,
            temperature=0.0,
        )

        choice = response.choices[0]
        finish_reason = choice.finish_reason

        # Extract tool calls if present
        tool_calls_data = None
        if choice.message.tool_calls:
            tool_calls_data = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.message.tool_calls
            ]

        # Record response
        response_event = LLMResponseEvent(
            model_id=response.model,
            content=choice.message.content,
            tool_calls=tool_calls_data,
            finish_reason=finish_reason,
            input_tokens=response.usage.prompt_tokens if response.usage else None,
            output_tokens=response.usage.completion_tokens if response.usage else None,
            request_hash=req_envelope.hash,
            provider_request_id=response.id,
            identity_context=identity,
            source=EventSource.CAPTURED,
        )
        resp_envelope = vault.append_event(response_event)
        print(f"[DEMO] Event {resp_envelope.seq}: LLM response ({finish_reason})")

        # Handle tool calls
        if finish_reason == "tool_calls" and choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)

                # Record and execute tool
                router.set_triggered_by(resp_envelope.seq)
                result = router.invoke(tool_name, tool_args)
                tool_call_count += 1
                print(f"[DEMO] Tool call: {tool_name}({tool_args})")

                # Add tool result to messages
                messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                        ],
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
        else:
            # Final response
            print(f"[DEMO] Final response: {choice.message.content[:100]}...")
            break

    # Finalize vault
    chain_head = vault.finalize()
    print()
    print(f"[DEMO] Session finalized. Chain head: {chain_head[:16]}...")
    print(f"[DEMO] Total tool calls: {tool_call_count}")

    # Run threat detection
    threat_flags = detect_threats(vault_path)
    print(f"[DEMO] Threat flags detected: {len(threat_flags)}")
    for flag in threat_flags:
        tags = ", ".join(t.value for t in flag.owasp_asi_tags)
        print(f"       [{flag.severity.value}] {flag.threat_class.value}: {tags}")

    # Export bundle with threat flags
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

    # Summary
    print()
    print("=" * 60)
    print("REAL CAPTURE DEMO SUMMARY")
    print("=" * 60)
    print(f"Bundle path: {bundle_path}")
    print("Event source: CAPTURED")
    print(f"Tool calls: {tool_call_count}")
    print(f"Threat flags: {len(threat_flags)}")
    print()
    print("To verify bundle:")
    print(f"  cd {bundle_path} && python verify.py")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Real Capture Demo")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./real_output"),
        help="Output directory",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock OpenAI client (default: True if no OPENAI_API_KEY)",
    )
    args = parser.parse_args()

    # Default to mock if no API key
    use_mock = args.mock or not os.environ.get("OPENAI_API_KEY")

    args.output.mkdir(parents=True, exist_ok=True)
    run_demo(args.output, use_mock=use_mock)


if __name__ == "__main__":
    main()
