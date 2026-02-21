"""Psychological context models for optional Lane B forensic linkage."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from aak.canon.hasher import domain_hash


class PsychContextSource(str, Enum):
    """Provenance of psychological context."""

    CAPTURED = "captured"
    SYNTHETIC = "synthetic"


class PsychCaptureMode(str, Enum):
    """Capture strategy for psychological context."""

    HASH_REF = "hash_ref"
    INLINE_MINIMAL = "inline_minimal"


class PsychIndicator(BaseModel):
    """Minimal elevated indicator payload."""

    indicator_id: str
    activation_level: float = Field(..., ge=0.0, le=100.0)
    category: str | None = None

    model_config = {"extra": "forbid"}


class PsychContext(BaseModel):
    """
    Optional psychological context attached to a captured event.

    This payload is evidence-only and does not carry authority semantics.
    """

    source: PsychContextSource = PsychContextSource.CAPTURED
    capture_mode: PsychCaptureMode = PsychCaptureMode.HASH_REF

    snapshot_id: str | None = None
    snapshot_timestamp: datetime | None = None
    convergence_score: float | None = Field(default=None, ge=0.0, le=1.0)

    elevated_categories: list[str] = Field(default_factory=list)
    elevated_indicators: list[PsychIndicator] = Field(default_factory=list)

    psych_root_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    reasoning_root_ref: str | None = None
    ui_root_ref: str | None = None

    artifact_path: str | None = None
    artifact_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def _validate_artifact_pair(self) -> "PsychContext":
        has_path = self.artifact_path is not None
        has_hash = self.artifact_hash is not None
        if has_path != has_hash:
            raise ValueError(
                "artifact_path and artifact_hash must be provided together for psych context"
            )

        if self.artifact_path is not None:
            path = Path(self.artifact_path)
            if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("psych",):
                raise ValueError("artifact_path must be a safe relative path under psych/")

        return self

    model_config = {"extra": "forbid"}


def psych_artifact_hash(payload: Any) -> str:
    """Canonical hash for a psych snapshot payload."""
    return domain_hash("manifest", payload)


__all__ = [
    "PsychCaptureMode",
    "PsychContext",
    "PsychContextSource",
    "PsychIndicator",
    "psych_artifact_hash",
]
