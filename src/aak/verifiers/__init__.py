"""Interfaces for external verifier integrations."""

from __future__ import annotations

from typing import Protocol

from aak.models.verifier import VerifierEvidence


class VerifierEvidenceProvider(Protocol):
    """Interface for collecting external verifier evidence."""

    def collect_evidence(self) -> list[VerifierEvidence]:
        """Return verifier evidence entries to include in an exported bundle."""


__all__ = ["VerifierEvidenceProvider"]
