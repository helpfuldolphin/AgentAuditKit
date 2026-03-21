"""Replay manifest model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from aak.models.events import EventEnvelope
from aak.models.psych import PsychCaptureMode, PsychContextSource
from aak.models.threats import ThreatFlag
from aak.models.verifier import VerifierEvidence


class AccountabilityMetadata(BaseModel):
    """Accountability metadata for the captured workflow."""

    requested_by: str | None = None
    approved_by: str | None = None
    environment: str | None = None
    policy_version: str | None = None

    model_config = {"extra": "forbid"}


class SessionMetadata(BaseModel):
    """Metadata about the capture session."""

    model_id: str | None = None
    provider: str | None = None
    workflow_id: str | None = None
    workflow_name: str | None = None
    sampling_params: dict[str, float | int | None] = Field(default_factory=dict)
    sdk_version: str
    interceptor_config: dict[str, Any] = Field(default_factory=dict)
    accountability: AccountabilityMetadata | None = None
    psych_context_enabled: bool = False
    psych_contract_version: str | None = None
    psych_provider: str | None = None
    psych_capture_mode: PsychCaptureMode | None = None
    psych_source: PsychContextSource | None = None
    verifier_contract_version: str | None = None

    model_config = {"extra": "forbid"}


class ReplayManifest(BaseModel):
    """
    Root manifest for exported replay bundle.

    Contains hash chain metadata and threat flags.
    """

    version: str = "0.3.0"
    bundle_id: str = Field(..., pattern=r"^run_[a-z0-9]{6,32}$")
    created_at: datetime

    # Hash chain
    chain_root: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    chain_head: str = Field(..., pattern=r"^[a-f0-9]{64}$")

    # Events
    events: list[EventEnvelope]
    event_count: int

    # Metadata
    metadata: SessionMetadata

    # Threat detection results
    threat_flags: list[ThreatFlag] = Field(default_factory=list)
    verifier_evidence: list[VerifierEvidence] = Field(default_factory=list)

    # Disclaimer (always present)
    disclaimer: str = Field(
        default=(
            "EVIDENCE ARTIFACT: This bundle is a forensic evidence artifact, NOT a "
            "compliance certification. Findings are heuristic-based. Hosted LLMs are "
            "non-deterministic; replay may produce different outputs. For governance-grade "
            "verification, see Lane A (MathLedger)."
        )
    )

    model_config = {"extra": "forbid"}
