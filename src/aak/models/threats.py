"""Threat detection models with OWASP Agentic mappings."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ThreatClass(str, Enum):
    """Threat classes detected by Agent Audit Kit."""

    TOOL_MISUSE = "TOOL_MISUSE"
    RAG_POISONING = "RAG_POISONING"
    PRIVILEGE_MISUSE = "PRIVILEGE_MISUSE"


class Severity(str, Enum):
    """Severity levels for threat flags."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OWASPAgenticTag(str, Enum):
    """
    OWASP Agentic Security Initiative (ASI) Top 10 mappings.
    https://owasp.org/www-project-top-10-for-large-language-model-applications/
    """

    ASI01 = "ASI01"  # Prompt Injection
    ASI02 = "ASI02"  # Insecure Tool/Plugin Design (Tool Misuse)
    ASI03 = "ASI03"  # Excessive Agency / Privilege Misuse
    ASI04 = "ASI04"  # Overreliance on LLM Outputs
    ASI05 = "ASI05"  # Supply Chain Vulnerabilities
    ASI06 = "ASI06"  # Sensitive Information Disclosure (RAG Poisoning vector)
    ASI07 = "ASI07"  # Insecure Output Handling
    ASI08 = "ASI08"  # Model Denial of Service
    ASI09 = "ASI09"  # Training Data Poisoning
    ASI10 = "ASI10"  # Unbounded Consumption


# Mapping from our threat classes to OWASP ASI tags
THREAT_CLASS_TO_ASI: dict[ThreatClass, list[OWASPAgenticTag]] = {
    ThreatClass.TOOL_MISUSE: [OWASPAgenticTag.ASI02, OWASPAgenticTag.ASI03],
    ThreatClass.RAG_POISONING: [OWASPAgenticTag.ASI01, OWASPAgenticTag.ASI06],
    ThreatClass.PRIVILEGE_MISUSE: [OWASPAgenticTag.ASI03],
}


class ThreatFlag(BaseModel):
    """
    Heuristic threat detection result.

    These are pattern-based detections, NOT formal proofs.
    is_heuristic is always True.
    """

    flag_id: str = Field(..., description="Unique identifier for this flag")
    threat_class: ThreatClass
    severity: Severity

    # OWASP Agentic mapping
    owasp_asi_tags: list[OWASPAgenticTag]

    # Evidence linkage
    event_seq: int = Field(..., description="Sequence number of flagged event")
    evidence_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")

    # Detection details
    description: str
    detector_id: str = Field(..., description="ID of detector that raised this flag")
    detector_version: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Heuristic confidence score")

    # Context
    detected_at: datetime
    raw_evidence: dict[str, Any] | None = Field(None, description="Relevant snippet of event data")

    # Non-claim discipline
    is_heuristic: bool = Field(
        default=True, description="Always True - these are not formal proofs"
    )

    model_config = {"extra": "forbid"}
