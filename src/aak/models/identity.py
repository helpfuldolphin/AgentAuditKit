"""Identity and permission context models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ActorType(str, Enum):
    """Type of actor invoking the agent."""

    HUMAN = "human"
    AGENT = "agent"
    SERVICE = "service"
    SYSTEM = "system"


class IdentityContext(BaseModel):
    """
    Non-human identity and permission context.
    Captured at event creation time.
    """

    actor_type: ActorType
    actor_id: str = Field(..., description="Unique identifier for the actor")
    actor_name: str | None = Field(None, description="Human-readable name")

    # Permission context
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    permission_source: str | None = Field(
        None,
        description="Where permissions were derived from (e.g., 'oauth_token', 'api_key')",
    )

    # Delegation chain (for multi-agent)
    delegated_by: str | None = Field(None, description="Actor ID that delegated to this actor")
    delegation_depth: int = Field(0, ge=0)

    # Session context
    session_id: str | None = None
    authenticated_at: datetime | None = None

    model_config = {"extra": "forbid"}
