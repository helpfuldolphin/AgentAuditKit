"""Unit tests for psych context models and hashing."""

from __future__ import annotations

import pytest

from aak.models.psych import PsychContext, PsychContextSource, PsychIndicator, psych_artifact_hash


def test_psych_context_defaults_to_hash_ref():
    context = PsychContext(source=PsychContextSource.CAPTURED)
    assert context.capture_mode.value == "hash_ref"


def test_psych_context_requires_artifact_path_and_hash_together():
    with pytest.raises(ValueError, match="artifact_path and artifact_hash"):
        PsychContext(artifact_path="psych/001.json")

    with pytest.raises(ValueError, match="artifact_path and artifact_hash"):
        PsychContext(artifact_hash="a" * 64)


def test_psych_context_requires_safe_artifact_path():
    with pytest.raises(ValueError, match="safe relative path"):
        PsychContext(
            artifact_path="../bad.json",
            artifact_hash="a" * 64,
        )

    with pytest.raises(ValueError, match="safe relative path"):
        PsychContext(
            artifact_path="events/001.json",
            artifact_hash="a" * 64,
        )


def test_psych_artifact_hash_is_deterministic():
    payload = {"snapshot_id": "spf_1030", "convergence_score": 0.2}
    assert psych_artifact_hash(payload) == psych_artifact_hash(payload)


def test_inline_minimal_context():
    context = PsychContext(
        capture_mode="inline_minimal",
        elevated_indicators=[
            PsychIndicator(indicator_id="1.3", activation_level=70.0, category="authority"),
            PsychIndicator(indicator_id="2.1", activation_level=55.0, category="temporal"),
        ],
    )
    assert context.capture_mode.value == "inline_minimal"
    assert len(context.elevated_indicators) == 2
