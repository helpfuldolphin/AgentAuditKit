"""
OpenAI ChatCompletions wrapper for real capture.

This wrapper intercepts OpenAI API calls and records them to the vault.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Callable

from aak.canon.hasher import domain_hash
from aak.intercept.psych_provider import PsychContextProvider
from aak.models.events import (
    EventSource,
    LLMRequestEvent,
    LLMResponseEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from aak.models.identity import IdentityContext
from aak.models.psych import PsychContext
from aak.vault.store import VaultWriter

if TYPE_CHECKING:
    from openai import OpenAI
    from openai.types.chat import ChatCompletion


class CapturedOpenAI:
    """
    OpenAI client wrapper that captures all ChatCompletion calls to a vault.

    Usage:
        from openai import OpenAI
        from aak.intercept import CapturedOpenAI

        client = CapturedOpenAI(
            OpenAI(),
            vault_path="./my_vault",
            identity_context=IdentityContext(...)
        )

        # Use like normal OpenAI client
        response = client.chat.completions.create(...)

        # Finalize and export
        client.finalize()
    """

    def __init__(
        self,
        client: OpenAI,
        vault_path: str,
        identity_context: IdentityContext | None = None,
        source: EventSource = EventSource.CAPTURED,
        psych_context_provider: PsychContextProvider | None = None,
    ) -> None:
        """
        Initialize captured OpenAI client.

        Args:
            client: The underlying OpenAI client.
            vault_path: Path to store captured events.
            identity_context: Identity context for captured events.
            source: Event source (captured or synthetic).
            psych_context_provider: Optional provider for psych context snapshots.
        """
        self._client = client
        self._vault = VaultWriter(vault_path)
        self._identity_context = identity_context
        self._source = source
        self._psych_context_provider = psych_context_provider
        self._last_request_hash: str | None = None

        # Create a chat.completions-like interface
        self.chat = _ChatNamespace(self)

    @property
    def run_id(self) -> str:
        """Current capture session ID."""
        return self._vault.run_id

    @property
    def vault(self) -> VaultWriter:
        """Access to the underlying vault writer."""
        return self._vault

    def finalize(self) -> str:
        """
        Finalize the capture session.

        Returns:
            Chain head hash.
        """
        return self._vault.finalize()

    def get_underlying_client(self) -> OpenAI:
        """Return the underlying OpenAI client."""
        return self._client

    def _get_psych_context(self) -> PsychContext | None:
        provider = self._psych_context_provider
        if provider is None:
            return None
        context = provider.get_current_context()
        if context is None:
            return None
        if isinstance(context, PsychContext):
            return context
        return PsychContext.model_validate(context)


class _ChatNamespace:
    """Namespace for chat.completions interface."""

    def __init__(self, captured: CapturedOpenAI) -> None:
        self._captured = captured
        self.completions = _CompletionsNamespace(captured)


class _CompletionsNamespace:
    """Namespace for chat.completions.create interface."""

    def __init__(self, captured: CapturedOpenAI) -> None:
        self._captured = captured

    def create(self, **kwargs: Any) -> ChatCompletion:
        """
        Create a chat completion and record to vault.

        Supports all standard OpenAI ChatCompletion parameters.
        """
        # Extract parameters for recording
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        temperature = kwargs.get("temperature")
        top_p = kwargs.get("top_p")
        max_tokens = kwargs.get("max_tokens")
        seed = kwargs.get("seed")
        tools = kwargs.get("tools")
        tool_choice = kwargs.get("tool_choice")

        # Record request event
        request_event = LLMRequestEvent(
            model_id=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            seed=seed,
            tools=tools,
            tool_choice=tool_choice,
            provider="openai",
            identity_context=self._captured._identity_context,
            psych_context=self._captured._get_psych_context(),
            source=self._captured._source,
        )
        request_envelope = self._captured._vault.append_event(request_event)
        self._captured._last_request_hash = request_envelope.hash

        # Make the actual API call
        start_time = time.time()
        response = self._captured._client.chat.completions.create(**kwargs)
        latency_ms = int((time.time() - start_time) * 1000)

        # Extract response data
        choice = response.choices[0] if response.choices else None
        content = choice.message.content if choice else None
        finish_reason = choice.finish_reason if choice else None

        # Extract tool calls if present
        tool_calls_data = None
        if choice and choice.message.tool_calls:
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

        # Record response event
        response_event = LLMResponseEvent(
            model_id=response.model,
            content=content,
            tool_calls=tool_calls_data,
            finish_reason=finish_reason,
            input_tokens=response.usage.prompt_tokens if response.usage else None,
            output_tokens=response.usage.completion_tokens if response.usage else None,
            request_hash=request_envelope.hash,
            provider_request_id=response.id,
            latency_ms=latency_ms,
            identity_context=self._captured._identity_context,
            psych_context=self._captured._get_psych_context(),
            source=self._captured._source,
        )
        self._captured._vault.append_event(response_event)

        return response


class ToolRouter:
    """
    Registry of tools that records calls to a vault.

    Usage:
        router = ToolRouter(vault, identity_context)
        router.register("search_kb", search_kb_function)
        result = router.invoke("search_kb", {"query": "test"})
    """

    def __init__(
        self,
        vault: VaultWriter,
        identity_context: IdentityContext | None = None,
        source: EventSource = EventSource.CAPTURED,
        psych_context_provider: PsychContextProvider | None = None,
    ) -> None:
        """
        Initialize tool router.

        Args:
            vault: Vault writer for recording.
            identity_context: Identity context for events.
            source: Event source (captured or synthetic).
            psych_context_provider: Optional provider for psych context snapshots.
        """
        self._vault = vault
        self._identity_context = identity_context
        self._source = source
        self._psych_context_provider = psych_context_provider
        self._tools: dict[str, Callable[..., Any]] = {}
        self._last_response_seq: int | None = None

    def _get_psych_context(self) -> PsychContext | None:
        provider = self._psych_context_provider
        if provider is None:
            return None
        context = provider.get_current_context()
        if context is None:
            return None
        if isinstance(context, PsychContext):
            return context
        return PsychContext.model_validate(context)

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        """Register a tool function."""
        self._tools[name] = fn

    def set_triggered_by(self, response_seq: int) -> None:
        """Set the LLM response sequence that triggered subsequent tool calls."""
        self._last_response_seq = response_seq

    def invoke(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        triggered_by_seq: int | None = None,
    ) -> Any:
        """
        Invoke a registered tool and record the call.

        Args:
            name: Tool name.
            arguments: Tool arguments.
            triggered_by_seq: Sequence of triggering LLM response.

        Returns:
            Tool result.

        Raises:
            KeyError: If tool not registered.
        """
        if name not in self._tools:
            raise KeyError(f"Tool not registered: {name}")

        # Record tool call event
        call_event = ToolCallEvent(
            tool_name=name,
            tool_input=arguments,
            tool_input_hash=domain_hash("tool_call", arguments),
            triggered_by_seq=triggered_by_seq or self._last_response_seq,
            identity_context=self._identity_context,
            psych_context=self._get_psych_context(),
            source=self._source,
        )
        call_envelope = self._vault.append_event(call_event)

        # Execute tool
        start_time = time.time()
        success = True
        error_message = None
        try:
            result = self._tools[name](**arguments)
        except Exception as e:
            success = False
            error_message = str(e)
            result = {"error": error_message}

        latency_ms = int((time.time() - start_time) * 1000)

        # Record tool result event
        result_event = ToolResultEvent(
            tool_name=name,
            tool_output=result,
            tool_output_hash=domain_hash("tool_result", result),
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
            call_seq=call_envelope.seq,
            identity_context=self._identity_context,
            psych_context=self._get_psych_context(),
            source=self._source,
        )
        self._vault.append_event(result_event)

        return result


def intercept_openai(
    client: OpenAI,
    vault_path: str,
    *,
    identity_context: IdentityContext | None = None,
    source: EventSource = EventSource.CAPTURED,
    psych_context_provider: PsychContextProvider | None = None,
) -> CapturedOpenAI:
    """
    Wrap an OpenAI client to capture all calls.

    Args:
        client: OpenAI client instance.
        vault_path: Path to store captured events.
        identity_context: Identity context for captured events.
        source: Event source (captured or synthetic).
        psych_context_provider: Optional provider for psych context snapshots.

    Returns:
        Wrapped client that records to vault.
    """
    return CapturedOpenAI(
        client,
        vault_path=vault_path,
        identity_context=identity_context,
        source=source,
        psych_context_provider=psych_context_provider,
    )
