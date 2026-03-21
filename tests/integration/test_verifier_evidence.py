"""Integration tests for optional verifier-evidence bundle support."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from aak.models.events import LLMRequestEvent
from aak.models.manifest import SessionMetadata
from aak.models.verifier import (
    VerifierEvidence,
    VerifierKind,
    VerifierStatus,
    verifier_artifact_hash,
)
from aak.replay import verify_bundle
from aak.vault.export import export_bundle
from aak.vault.store import VaultWriter


def _make_verifier_bundle(tmp_path: Path) -> Path:
    vault_path = tmp_path / "vault"
    bundle_path = tmp_path / "bundle"

    writer = VaultWriter(vault_path)
    writer.append_event(
        LLMRequestEvent(
            model_id="gpt-4o",
            messages=[{"role": "user", "content": "Verify claim CLM-001"}],
            provider="openai",
        )
    )
    writer.finalize()

    verifier_dir = vault_path / "verifiers"
    verifier_dir.mkdir(parents=True, exist_ok=True)
    artifact_payload = {
        "claim_id": "CLM-001",
        "prover": "leanstral-sim",
        "status": "verified",
        "proof_hash": "c" * 64,
    }
    artifact_path = verifier_dir / "000_clm_001.json"
    artifact_path.write_text(
        json.dumps(artifact_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    export_bundle(
        vault_path,
        bundle_path,
        session_metadata=SessionMetadata(sdk_version="0.3.0"),
        verifier_evidence=[
            VerifierEvidence(
                claim_id="CLM-001",
                verifier_id="leanstral-sim",
                verifier_kind=VerifierKind.FORMAL_PROVER,
                status=VerifierStatus.VERIFIED,
                verified_at=datetime.now(timezone.utc),
                proof_hash="c" * 64,
                artifact_path="verifiers/000_clm_001.json",
                artifact_hash=verifier_artifact_hash(artifact_payload),
                toolchain="lean4 + leanstral",
            )
        ],
    )
    return bundle_path


def test_verifier_bundle_verifies(tmp_path: Path):
    bundle_path = _make_verifier_bundle(tmp_path)
    result = verify_bundle(bundle_path)
    assert result.valid is True


def test_verifier_bundle_fails_closed_on_extra_artifact(tmp_path: Path):
    bundle_path = _make_verifier_bundle(tmp_path)
    extra_path = bundle_path / "verifiers" / "999_extra.json"
    extra_path.write_text('{"extra": true}', encoding="utf-8")

    result = verify_bundle(bundle_path)
    assert result.valid is False
    assert "extra verifier artifacts" in result.message
