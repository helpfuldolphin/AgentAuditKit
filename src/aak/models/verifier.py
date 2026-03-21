"""Verifier-evidence models for optional external proof artifacts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from aak.canon.hasher import domain_hash


class VerifierKind(str, Enum):
    """High-level verifier categories."""

    FORMAL_PROVER = "formal_prover"
    MODEL_CHECKER = "model_checker"
    STATIC_ANALYZER = "static_analyzer"
    TYPE_CHECKER = "type_checker"
    OTHER = "other"


class VerifierStatus(str, Enum):
    """Verification result state."""

    VERIFIED = "verified"
    FAILED = "failed"
    ABSTAINED = "abstained"
    UNKNOWN = "unknown"


class VerifierEvidence(BaseModel):
    """Manifest-level reference to external verifier evidence."""

    claim_id: str
    verifier_id: str
    verifier_kind: VerifierKind = VerifierKind.FORMAL_PROVER
    status: VerifierStatus = VerifierStatus.UNKNOWN
    verified_at: datetime

    proof_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    artifact_path: str | None = None
    artifact_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    toolchain: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_artifact_pair(self) -> "VerifierEvidence":
        has_path = self.artifact_path is not None
        has_hash = self.artifact_hash is not None
        if has_path != has_hash:
            raise ValueError(
                "artifact_path and artifact_hash must be provided together for verifier evidence"
            )

        if self.artifact_path is not None:
            path = Path(self.artifact_path)
            if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("verifiers",):
                raise ValueError("artifact_path must be a safe relative path under verifiers/")

        return self

    model_config = {"extra": "forbid"}


def verifier_artifact_hash(payload: object) -> str:
    """Canonical hash for a verifier artifact payload."""

    return domain_hash("manifest", payload)


__all__ = [
    "VerifierEvidence",
    "VerifierKind",
    "VerifierStatus",
    "verifier_artifact_hash",
]
