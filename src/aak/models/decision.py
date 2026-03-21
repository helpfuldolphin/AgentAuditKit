"""Decision-context models for exhibit-grade decision lineage."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DecisionContextSource(str, Enum):
    """Provenance of decision-context data."""

    CAPTURED = "captured"
    SYNTHETIC = "synthetic"


class ConfidenceSignal(BaseModel):
    """Recorded confidence signal or explicit absence marker."""

    signal_id: str
    label: str
    value: float | None = Field(default=None, ge=0.0, le=1.0)
    status: str = Field(default="present")
    note: str | None = None
    source_ref: str | None = None

    model_config = {"extra": "forbid"}


class ContextReference(BaseModel):
    """Reference to an upstream input or supporting artifact."""

    ref_type: str
    label: str
    ref: str
    ref_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    note: str | None = None

    model_config = {"extra": "forbid"}


class DecisionContextSnapshot(BaseModel):
    """Recorded decision context at a decision boundary."""

    source: DecisionContextSource = DecisionContextSource.CAPTURED
    snapshot_id: str | None = None
    captured_at: datetime | None = None

    requested_by: str | None = None
    approved_by: str | None = None
    environment: str | None = None
    policy_version: str | None = None

    action_summary: str | None = None
    reversible: bool | None = None

    perceived_world_state: list[str] = Field(default_factory=list)
    upstream_inputs: list[str] = Field(default_factory=list)
    confidence_signals: list[ConfidenceSignal] = Field(default_factory=list)
    missing_confidence_signals: list[str] = Field(default_factory=list)
    context_references: list[ContextReference] = Field(default_factory=list)
    counterfactual_checks: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = [
    "ConfidenceSignal",
    "ContextReference",
    "DecisionContextSnapshot",
    "DecisionContextSource",
]
