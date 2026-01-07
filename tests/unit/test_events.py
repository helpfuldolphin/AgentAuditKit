"""Unit tests for event models."""

from datetime import datetime, timezone

from aak.models.events import (
    EventSource,
    EventType,
    LLMRequestEvent,
    LLMResponseEvent,
    SessionStartEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from aak.models.identity import ActorType, IdentityContext


class TestEventModels:
    """Test suite for event models."""

    def test_event_source_default_captured(self):
        """EventBase defaults to captured source."""
        event = SessionStartEvent(
            run_id="run_test123",
            sdk_version="0.1.0",
            vault_path="/tmp/vault",
        )
        assert event.source == EventSource.CAPTURED

    def test_event_source_synthetic(self):
        """Events can be marked as synthetic."""
        event = SessionStartEvent(
            run_id="run_test123",
            sdk_version="0.1.0",
            vault_path="/tmp/vault",
            source=EventSource.SYNTHETIC,
        )
        assert event.source == EventSource.SYNTHETIC

    def test_llm_request_event(self):
        """LLMRequestEvent captures request details."""
        event = LLMRequestEvent(
            model_id="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            provider="openai",
        )
        assert event.event_type == EventType.LLM_REQUEST
        assert event.model_id == "gpt-4"
        assert event.temperature == 0.7

    def test_llm_response_event(self):
        """LLMResponseEvent captures response details."""
        event = LLMResponseEvent(
            model_id="gpt-4",
            content="Hello there!",
            finish_reason="stop",
            request_hash="a" * 64,
            input_tokens=10,
            output_tokens=5,
        )
        assert event.event_type == EventType.LLM_RESPONSE
        assert event.content == "Hello there!"

    def test_tool_call_event(self):
        """ToolCallEvent captures tool invocation."""
        event = ToolCallEvent(
            tool_name="search",
            tool_input={"query": "test"},
            tool_input_hash="b" * 64,
        )
        assert event.event_type == EventType.TOOL_CALL
        assert event.tool_name == "search"

    def test_tool_result_event(self):
        """ToolResultEvent captures tool result."""
        event = ToolResultEvent(
            tool_name="search",
            tool_output={"results": []},
            tool_output_hash="c" * 64,
            latency_ms=100,
            success=True,
            call_seq=1,
        )
        assert event.event_type == EventType.TOOL_RESULT
        assert event.success is True

    def test_identity_context_attached(self):
        """Events can have identity context."""
        identity = IdentityContext(
            actor_type=ActorType.AGENT,
            actor_id="agent-001",
            roles=["assistant"],
            permissions=["read"],
        )
        event = SessionStartEvent(
            run_id="run_test",
            sdk_version="0.1.0",
            vault_path="/tmp",
            identity_context=identity,
        )
        assert event.identity_context is not None
        assert event.identity_context.actor_id == "agent-001"
        assert event.identity_context.actor_type == ActorType.AGENT

    def test_event_timestamp_default(self):
        """Events get automatic timestamp."""
        before = datetime.now(timezone.utc)
        event = SessionStartEvent(
            run_id="run_test",
            sdk_version="0.1.0",
            vault_path="/tmp",
        )
        after = datetime.now(timezone.utc)
        assert before <= event.timestamp <= after

    def test_event_serialization(self):
        """Events serialize to JSON correctly."""
        event = LLMRequestEvent(
            model_id="gpt-4",
            messages=[{"role": "user", "content": "Hi"}],
            provider="openai",
            source=EventSource.SYNTHETIC,
        )
        data = event.model_dump(mode="json")
        assert data["event_type"] == "llm_request"
        assert data["source"] == "synthetic"
        assert data["model_id"] == "gpt-4"
