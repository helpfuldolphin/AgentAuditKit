"""Replay manifest model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from aak.models.events import EventEnvelope
from aak.models.psych import PsychCaptureMode, PsychContextSource
from aak.models.threats import ThreatFlag


class SessionMetadata(BaseModel):
    """Metadata about the capture session."""

    model_id: str | None = None
    provider: str | None = None
    sampling_params: dict[str, float | int | None] = Field(default_factory=dict)
    sdk_version: str
    interceptor_config: dict[str, Any] = Field(default_factory=dict)
    psych_context_enabled: bool = False
    psych_contract_version: str | None = None
    psych_provider: str | None = None
    psych_capture_mode: PsychCaptureMode | None = None
    psych_source: PsychContextSource | None = None

    model_config = {"extra": "forbid"}


class ReplayManifest(BaseModel):
    """
    Root manifest for exported replay bundle.

    Contains hash chain metadata and threat flags.
    """

    version: str = "0.1.0"
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
