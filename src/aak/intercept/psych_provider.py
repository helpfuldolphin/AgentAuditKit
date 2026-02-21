"""Psychological context provider protocol for optional capture enrichment."""

from __future__ import annotations

from typing import Protocol

from aak.models.psych import PsychContext


class PsychContextProvider(Protocol):
    """Provider interface for retrieving current psych context."""

    def get_current_context(self) -> PsychContext | None:
        """Return current psych context to attach to the next event."""


__all__ = ["PsychContextProvider"]
