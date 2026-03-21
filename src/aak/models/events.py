"""Event models for Agent Audit Kit."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from aak.models.decision import DecisionContextSnapshot
from aak.models.identity import IdentityContext
from aak.models.psych import PsychContext


class EventType(str, Enum):
    """Types of events that can be captured."""

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    RAG_RETRIEVAL = "rag_retrieval"
    RAG_CHUNK = "rag_chunk"


class EventSource(str, Enum):
    """Provenance of the event."""

    CAPTURED = "captured"  # Real event from live system
    SYNTHETIC = "synthetic"  # Generated for demo/testing


class EventBase(BaseModel):
    """
    Base class for all captured events.

    The event_hash is computed over the canonical JSON of this payload,
    EXCLUDING envelope fields (seq, hash, prev_hash, payload_file).
    """

    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    identity_context: IdentityContext | None = None
    decision_context: DecisionContextSnapshot | None = None
    psych_context: PsychContext | None = None

    # Provenance labeling (REQUIRED for non-claims discipline)
    source: EventSource = Field(
        default=EventSource.CAPTURED,
        description="Whether event was captured from live system or synthetic",
    )

    model_config = {"extra": "forbid"}


class EventEnvelope(BaseModel):
    """
    Wrapper with hash chain metadata.

    These fields are NOT included in the event hash computation.
    They are metadata about the event's position in the chain.
    """

    seq: int = Field(..., ge=0)
    event_type: EventType
    hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    prev_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    timestamp: datetime
    payload_file: str  # Relative path to event JSON

    model_config = {"extra": "forbid"}


# --- Event Subtypes ---


class SessionStartEvent(EventBase):
    """Marks the start of a capture session."""

    event_type: Literal[EventType.SESSION_START] = EventType.SESSION_START
    run_id: str
    sdk_version: str
    vault_path: str


class SessionEndEvent(EventBase):
    """Marks the end of a capture session."""

    event_type: Literal[EventType.SESSION_END] = EventType.SESSION_END
    run_id: str
    event_count: int
    chain_head: str


class LLMRequestEvent(EventBase):
    """Captures an LLM API request."""

    event_type: Literal[EventType.LLM_REQUEST] = EventType.LLM_REQUEST
    model_id: str
    messages: list[dict[str, Any]]

    # Sampling parameters
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    seed: int | None = None

    # Tools offered
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None

    # Provider metadata
    provider: str  # "openai", "anthropic", etc.
    request_id: str | None = None


class LLMResponseEvent(EventBase):
    """Captures an LLM API response."""

    event_type: Literal[EventType.LLM_RESPONSE] = EventType.LLM_RESPONSE
    model_id: str

    # Response content
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str | None = None

    # Usage
    input_tokens: int | None = None
    output_tokens: int | None = None

    # Linkage
    request_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    provider_request_id: str | None = None
    latency_ms: int | None = None


class ToolCallEvent(EventBase):
    """Captures a tool invocation."""

    event_type: Literal[EventType.TOOL_CALL] = EventType.TOOL_CALL
    tool_name: str
    tool_input: dict[str, Any]
    tool_input_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")

    # Linkage to LLM response that triggered this
    triggered_by_seq: int | None = None


class ToolResultEvent(EventBase):
    """Captures a tool result."""

    event_type: Literal[EventType.TOOL_RESULT] = EventType.TOOL_RESULT
    tool_name: str
    tool_output: Any
    tool_output_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")

    # Performance
    latency_ms: int
    success: bool
    error_message: str | None = None

    # Linkage
    call_seq: int  # Sequence number of corresponding ToolCallEvent


class RAGRetrievalEvent(EventBase):
    """Captures a RAG retrieval operation."""

    event_type: Literal[EventType.RAG_RETRIEVAL] = EventType.RAG_RETRIEVAL
    query: str
    query_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    chunk_count: int
    chunk_hashes: list[str]
    retriever_id: str | None = None
    latency_ms: int | None = None


class RAGChunkEvent(EventBase):
    """Captures a single RAG chunk."""

    event_type: Literal[EventType.RAG_CHUNK] = EventType.RAG_CHUNK
    chunk_index: int
    chunk_text: str
    chunk_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    source_id: str | None = None
    retrieval_seq: int  # Linkage to RAGRetrievalEvent
