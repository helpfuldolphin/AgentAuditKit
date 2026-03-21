"""Built-in capture workflows for AAK."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

from aak import __version__
from aak.intercept import CapturedOpenAI, ToolRouter
from aak.models.decision import (
    ConfidenceSignal,
    ContextReference,
    DecisionContextSnapshot,
    DecisionContextSource,
)
from aak.models.events import EventSource, SessionStartEvent
from aak.models.identity import ActorType, IdentityContext
from aak.models.manifest import AccountabilityMetadata, SessionMetadata
from aak.vault.export import export_bundle


@dataclass(frozen=True)
class CaptureRunConfig:
    """Capture configuration for built-in scenarios."""

    scenario: str = "banking_decision_exposure"
    workflow_id: str = "wire_review_high_value"
    workflow_name: str = "Banking Decision Exposure Review"
    requested_by: str = "treasury_ops_queue"
    approved_by: str = "UNKNOWN"
    environment: str = "banking-prod-sim"
    policy_version: str = "wire_policy_v3"
    run_id: str | None = None
    clock_start: str | None = None
    clock_step_seconds: int = 1
    seed: int = 11


@dataclass(frozen=True)
class CaptureRunResult:
    """Output metadata for capture runs."""

    bundle_path: Path
    vault_path: Path
    event_count: int
    workflow_id: str


class _MutableDecisionContextProvider:
    """Simple mutable provider for staged decision-context snapshots."""

    def __init__(self) -> None:
        self._current: DecisionContextSnapshot | None = None

    def set_current(self, context: DecisionContextSnapshot) -> None:
        self._current = context

    def get_current_context(self) -> DecisionContextSnapshot | None:
        return self._current


class _StepClock:
    """Deterministic timestamp provider for golden-run generation."""

    def __init__(self, start: datetime, *, step_seconds: int = 1) -> None:
        self._current = start
        self._step_seconds = step_seconds

    def __call__(self) -> datetime:
        value = self._current
        self._current = value + timedelta(seconds=self._step_seconds)
        return value


class _FakeToolFunction:
    def __init__(self, name: str, arguments: str) -> None:
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, tool_call_id: str, name: str, arguments: str) -> None:
        self.id = tool_call_id
        self.type = "function"
        self.function = _FakeToolFunction(name, arguments)


class _FakeMessage:
    def __init__(self, content: str | None, tool_calls: list[_FakeToolCall] | None = None) -> None:
        self.content = content
        self.tool_calls = tool_calls or []


class _FakeChoice:
    def __init__(self, message: _FakeMessage, finish_reason: str) -> None:
        self.message = message
        self.finish_reason = finish_reason


class _FakeUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class _FakeResponse:
    def __init__(
        self,
        *,
        response_id: str,
        model: str,
        content: str | None,
        finish_reason: str,
        prompt_tokens: int,
        completion_tokens: int,
        tool_calls: list[_FakeToolCall] | None = None,
    ) -> None:
        self.id = response_id
        self.model = model
        self.choices = [_FakeChoice(_FakeMessage(content, tool_calls), finish_reason)]
        self.usage = _FakeUsage(prompt_tokens, completion_tokens)


class _FakeChatCompletions:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = responses
        self._index = 0

    def create(self, **kwargs: Any) -> _FakeResponse:
        if self._index >= len(self._responses):
            raise RuntimeError("No more fake responses configured for capture scenario")
        response = self._responses[self._index]
        self._index += 1
        return response


class _FakeChat:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.completions = _FakeChatCompletions(responses)


class _FakeOpenAIClient:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.chat = _FakeChat(responses)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _parse_scalar(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith('"') and cleaned.endswith('"') and len(cleaned) >= 2:
        return cleaned[1:-1]
    if cleaned.startswith("'") and cleaned.endswith("'") and len(cleaned) >= 2:
        return cleaned[1:-1]
    return cleaned


def parse_capture_config(config_path: str | Path) -> CaptureRunConfig:
    """Parse a small key/value capture config."""

    path = Path(config_path)
    raw_text = path.read_text(encoding="utf-8")
    stripped = raw_text.strip()
    if not stripped:
        return CaptureRunConfig()

    payload: dict[str, str] = {}
    if stripped.startswith("{"):
        loaded = json.loads(stripped)
        if not isinstance(loaded, dict):
            raise ValueError("Capture config JSON root must be an object")
        payload = {str(key): str(value) for key, value in loaded.items()}
    else:
        for line in raw_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            payload[key.strip()] = _parse_scalar(value)

    defaults = CaptureRunConfig()
    return CaptureRunConfig(
        scenario=payload.get("scenario", defaults.scenario),
        workflow_id=payload.get("workflow_id", defaults.workflow_id),
        workflow_name=payload.get("workflow_name", defaults.workflow_name),
        requested_by=payload.get("requested_by", defaults.requested_by),
        approved_by=payload.get("approved_by", defaults.approved_by),
        environment=payload.get("environment", defaults.environment),
        policy_version=payload.get("policy_version", defaults.policy_version),
        run_id=payload.get("run_id", defaults.run_id),
        clock_start=payload.get("clock_start", defaults.clock_start),
        clock_step_seconds=int(payload.get("clock_step_seconds", defaults.clock_step_seconds)),
        seed=int(payload.get("seed", defaults.seed)),
    )


def _decision_context(
    *,
    config: CaptureRunConfig,
    captured_at: datetime,
    snapshot_id: str,
    action_summary: str,
    reversible: bool,
    perceived_world_state: list[str],
    upstream_inputs: list[str],
    missing_confidence_signals: list[str],
    counterfactual_checks: list[str],
) -> DecisionContextSnapshot:
    return DecisionContextSnapshot(
        source=DecisionContextSource.CAPTURED,
        snapshot_id=snapshot_id,
        captured_at=captured_at,
        requested_by=config.requested_by,
        approved_by=None if config.approved_by == "UNKNOWN" else config.approved_by,
        environment=config.environment,
        policy_version=config.policy_version,
        action_summary=action_summary,
        reversible=reversible,
        perceived_world_state=perceived_world_state,
        upstream_inputs=upstream_inputs,
        missing_confidence_signals=missing_confidence_signals,
        counterfactual_checks=counterfactual_checks,
        confidence_signals=[
            ConfidenceSignal(
                signal_id="vendor_match_score",
                label="vendor_match_score",
                value=0.42,
                status="present",
                note="Vendor bank account changed within 24 hours.",
                source_ref="tool:lookup_vendor_profile",
            )
        ],
        context_references=[
            ContextReference(
                ref_type="workflow",
                label="payment_review_id",
                ref="PAY-2026-0319-771",
            ),
            ContextReference(
                ref_type="policy",
                label="policy",
                ref=config.policy_version,
            ),
        ],
    )


def _build_fake_client() -> _FakeOpenAIClient:
    return _FakeOpenAIClient(
        [
            _FakeResponse(
                response_id="resp_wire_001",
                model="gpt-4o-2026-03-01",
                content=None,
                finish_reason="tool_calls",
                prompt_tokens=220,
                completion_tokens=28,
                tool_calls=[
                    _FakeToolCall(
                        "call_vendor_lookup",
                        "lookup_vendor_profile",
                        '{"payment_id":"PAY-2026-0319-771"}',
                    )
                ],
            ),
            _FakeResponse(
                response_id="resp_wire_002",
                model="gpt-4o-2026-03-01",
                content=None,
                finish_reason="tool_calls",
                prompt_tokens=310,
                completion_tokens=32,
                tool_calls=[
                    _FakeToolCall(
                        "call_policy_check",
                        "check_policy_controls",
                        '{"amount_usd":245000,"bank_account_age_days":1,"dual_approval_present":false}',
                    )
                ],
            ),
            _FakeResponse(
                response_id="resp_wire_003",
                model="gpt-4o-2026-03-01",
                content=(
                    "Recommendation: hold release and require dual approval plus out-of-band "
                    "vendor confirmation before any funds movement."
                ),
                finish_reason="stop",
                prompt_tokens=355,
                completion_tokens=44,
            ),
        ]
    )


def _run_banking_decision_exposure(config: CaptureRunConfig, output_path: Path) -> CaptureRunResult:
    vault_path = output_path / "vault"
    bundle_path = output_path / "bundle"

    decision_provider = _MutableDecisionContextProvider()
    timestamp_provider = None
    if config.clock_start is not None:
        timestamp_provider = _StepClock(
            _parse_datetime(config.clock_start),
            step_seconds=config.clock_step_seconds,
        )
    identity_context = IdentityContext(
        actor_type=ActorType.AGENT,
        actor_id="treasury-review-agent",
        actor_name="Treasury Review Agent",
        roles=["payment_review", "treasury_ops"],
        permissions=["read:payments", "read:vendor_profile", "read:policy_controls"],
        permission_source="workflow_policy",
    )
    client = CapturedOpenAI(
        cast(Any, _build_fake_client()),
        vault_path=str(vault_path),
        identity_context=identity_context,
        source=EventSource.CAPTURED,
        decision_context_provider=decision_provider,
        run_id=config.run_id,
        timestamp_provider=timestamp_provider,
    )
    router = ToolRouter(
        client.vault,
        identity_context=identity_context,
        source=EventSource.CAPTURED,
        decision_context_provider=decision_provider,
        timestamp_provider=timestamp_provider,
    )

    def lookup_vendor_profile(payment_id: str) -> dict[str, Any]:
        return {
            "payment_id": payment_id,
            "vendor_name": "North Harbor Logistics",
            "amount_usd": 245000,
            "beneficiary_account_changed_within_days": 1,
            "beneficiary_change_ticket": "BNK-8812",
            "dual_approval_present": False,
        }

    def check_policy_controls(
        amount_usd: int,
        bank_account_age_days: int,
        dual_approval_present: bool,
    ) -> dict[str, Any]:
        return {
            "amount_usd": amount_usd,
            "bank_account_age_days": bank_account_age_days,
            "dual_approval_present": dual_approval_present,
            "requires_dual_approval": True,
            "requires_out_of_band_confirmation": True,
            "recommended_action": "hold_for_review",
        }

    router.register("lookup_vendor_profile", lookup_vendor_profile)
    router.register("check_policy_controls", check_policy_controls)

    def next_context_time() -> datetime:
        if timestamp_provider is None:
            return _utc_now()
        return timestamp_provider()

    client.vault.append_event(
        SessionStartEvent(
            run_id=client.run_id,
            sdk_version=__version__,
            vault_path="vault",
            timestamp=next_context_time(),
            identity_context=identity_context,
            source=EventSource.CAPTURED,
        )
    )

    decision_provider.set_current(
        _decision_context(
            config=config,
            captured_at=next_context_time(),
            snapshot_id="wire_review_intake",
            action_summary="Review high-value vendor wire release request",
            reversible=True,
            perceived_world_state=[
                "Payment amount exceeds standard auto-release threshold.",
                "Vendor beneficiary account changed within the last 24 hours.",
            ],
            upstream_inputs=[
                "payment_queue: PAY-2026-0319-771",
                "request channel: treasury operations queue",
            ],
            missing_confidence_signals=["out_of_band_vendor_confirmation"],
            counterfactual_checks=[
                "Confirm whether an independent vendor callback occurred before release.",
                "Confirm whether a second approver should have been present at intake.",
            ],
        )
    )
    client.chat.completions.create(
        model="gpt-4o-2026-03-01",
        messages=[
            {
                "role": "system",
                "content": (
                    "You review high-value vendor payment requests and document review actions."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Review payment PAY-2026-0319-771 before release. Record risk factors and "
                    "request any needed checks."
                ),
            },
        ],
        temperature=0.0,
        tools=[
            {"type": "function", "function": {"name": "lookup_vendor_profile"}},
            {"type": "function", "function": {"name": "check_policy_controls"}},
        ],
    )
    router.set_triggered_by(len(client.vault.get_envelopes()) - 1)

    decision_provider.set_current(
        _decision_context(
            config=config,
            captured_at=next_context_time(),
            snapshot_id="wire_review_vendor_lookup",
            action_summary="Inspect vendor profile and beneficiary change details",
            reversible=True,
            perceived_world_state=[
                "Vendor profile lookup is pending.",
                "No secondary approval has been recorded yet.",
            ],
            upstream_inputs=[
                "tool request: lookup_vendor_profile",
            ],
            missing_confidence_signals=["secondary_approval_record"],
            counterfactual_checks=[
                "Check whether the beneficiary change ticket was independently validated.",
            ],
        )
    )
    vendor_result = router.invoke("lookup_vendor_profile", {"payment_id": "PAY-2026-0319-771"})

    decision_provider.set_current(
        _decision_context(
            config=config,
            captured_at=next_context_time(),
            snapshot_id="wire_review_policy_check",
            action_summary="Evaluate release controls against recorded risk factors",
            reversible=True,
            perceived_world_state=[
                "Vendor profile shows a recent beneficiary-account change.",
                "No dual approval is present for the release request.",
            ],
            upstream_inputs=[
                "tool result: lookup_vendor_profile",
                "policy baseline: wire controls",
            ],
            missing_confidence_signals=["dual_approval_record", "out_of_band_vendor_confirmation"],
            counterfactual_checks=[
                "Check whether policy required an automatic hold on recent beneficiary changes.",
            ],
        )
    )
    client.chat.completions.create(
        model="gpt-4o-2026-03-01",
        messages=[
            {
                "role": "system",
                "content": "Use policy controls before any release recommendation.",
            },
            {
                "role": "user",
                "content": json.dumps(vendor_result, sort_keys=True),
            },
        ],
        temperature=0.0,
        tools=[
            {"type": "function", "function": {"name": "check_policy_controls"}},
        ],
    )
    router.set_triggered_by(len(client.vault.get_envelopes()) - 1)
    policy_result = router.invoke(
        "check_policy_controls",
        {
            "amount_usd": 245000,
            "bank_account_age_days": 1,
            "dual_approval_present": False,
        },
    )

    decision_provider.set_current(
        _decision_context(
            config=config,
            captured_at=next_context_time(),
            snapshot_id="wire_review_outcome",
            action_summary="Issue hold/review recommendation before funds movement",
            reversible=True,
            perceived_world_state=[
                "Policy controls recommend hold_for_review.",
                "Release can still be paused before any funds movement.",
            ],
            upstream_inputs=[
                "tool result: check_policy_controls",
                "decision path: release recommendation",
            ],
            missing_confidence_signals=["out_of_band_vendor_confirmation"],
            counterfactual_checks=[
                (
                    "Check whether the release would remain paused until confirmation "
                    "and approval are present."
                ),
            ],
        )
    )
    client.chat.completions.create(
        model="gpt-4o-2026-03-01",
        messages=[
            {
                "role": "system",
                "content": "Return a final release recommendation for the queue operator.",
            },
            {
                "role": "user",
                "content": json.dumps(policy_result, sort_keys=True),
            },
        ],
        temperature=0.0,
    )

    client.finalize()

    metadata = SessionMetadata(
        model_id="gpt-4o-2026-03-01",
        provider="openai",
        workflow_id=config.workflow_id,
        workflow_name=config.workflow_name,
        sdk_version=__version__,
        sampling_params={"temperature": 0.0},
        interceptor_config={"scenario_seed": config.seed},
        accountability=AccountabilityMetadata(
            requested_by=config.requested_by,
            approved_by=None if config.approved_by == "UNKNOWN" else config.approved_by,
            environment=config.environment,
            policy_version=config.policy_version,
        ),
    )
    export_bundle(vault_path, bundle_path, include_verify_script=True, session_metadata=metadata)

    return CaptureRunResult(
        bundle_path=bundle_path,
        vault_path=vault_path,
        event_count=len(client.vault.get_envelopes()),
        workflow_id=config.workflow_id,
    )


def run_capture_from_config(config_path: str | Path, output_path: str | Path) -> CaptureRunResult:
    """Run a built-in capture workflow from config."""

    config = parse_capture_config(config_path)
    output_path_obj = Path(output_path)
    output_path_obj.mkdir(parents=True, exist_ok=True)

    if config.scenario == "banking_decision_exposure":
        return _run_banking_decision_exposure(config, output_path_obj)

    raise ValueError(f"Unsupported capture scenario: {config.scenario}")
