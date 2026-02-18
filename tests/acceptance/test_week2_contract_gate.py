"""Week 2 contract gate tests for schema and naming consistency."""

from __future__ import annotations

import json
from pathlib import Path

from aak.models.events import LLMRequestEvent
from aak.vault.export import export_bundle
from aak.vault.store import VaultWriter


def test_schema_contract_freeze_doc_exists():
    """Schema contract doc must exist and mark bundle_id as canonical."""
    contract_path = Path("docs/contracts/SCHEMA_CONTRACT_V0_1.md")
    assert contract_path.exists()
    text = contract_path.read_text(encoding="utf-8")
    assert "bundle_id" in text
    assert "canonical" in text.lower()


def test_export_manifest_uses_bundle_id(tmp_path: Path):
    """Exported manifests use bundle_id as the canonical run identity field."""
    vault_path = tmp_path / "vault"
    bundle_path = tmp_path / "bundle"

    writer = VaultWriter(vault_path)
    writer.append_event(
        LLMRequestEvent(
            model_id="gpt-4",
            messages=[{"role": "user", "content": "week2 contract gate"}],
            provider="openai",
        )
    )
    writer.finalize()

    export_bundle(vault_path, bundle_path)
    manifest = json.loads((bundle_path / "replay_manifest.json").read_text(encoding="utf-8"))

    assert "bundle_id" in manifest
    assert manifest["bundle_id"].startswith("run_")
    assert "run_id" not in manifest


def test_demo_scripts_use_bundle_id_reference():
    """Demo scripts should reference bundle_id when reading manifest identity."""
    ps1_text = Path("demo/run_demo.ps1").read_text(encoding="utf-8")
    sh_text = Path("demo/run_demo.sh").read_text(encoding="utf-8")

    assert "bundle_id" in ps1_text
    assert "bundle_id" in sh_text
