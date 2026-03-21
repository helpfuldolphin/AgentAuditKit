"""Decision-context provider protocol for optional live capture enrichment."""

from __future__ import annotations

from typing import Protocol

from aak.models.decision import DecisionContextSnapshot


class DecisionContextProvider(Protocol):
    """Provider interface for retrieving current decision context."""

    def get_current_context(self) -> DecisionContextSnapshot | None:
        """Return current decision context to attach to the next event."""


__all__ = ["DecisionContextProvider"]
