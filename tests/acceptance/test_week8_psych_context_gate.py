"""Acceptance tests for optional psych-context evidence linkage."""

from __future__ import annotations

import json
from pathlib import Path

from aak.models.events import EventSource, LLMRequestEvent, SessionStartEvent
from aak.models.psych import PsychCaptureMode, PsychContext, PsychContextSource, psych_artifact_hash
from aak.replay import verify_bundle
from aak.report import generate_audit_report
from aak.vault.export import export_bundle
from aak.vault.store import VaultWriter


def _make_psych_bundle(tmp_path: Path) -> Path:
    vault_path = tmp_path / "vault"
    bundle_path = tmp_path / "bundle"

    writer = VaultWriter(vault_path)
    writer.append_event(
        SessionStartEvent(
            run_id=writer.run_id,
            sdk_version="0.1.0",
            vault_path=str(vault_path),
            source=EventSource.CAPTURED,
        )
    )

    psych_payload = {
        "snapshot_id": "spf_1100",
        "timestamp": "2026-02-21T11:00:00Z",
        "convergence_score": 0.75,
        "elevated_categories": ["authority", "temporal"],
        "governance_decision": "block_pending_multi_party_review",
    }
    psych_hash = psych_artifact_hash(psych_payload)

    writer.append_event(
        LLMRequestEvent(
            model_id="gpt-4",
            messages=[{"role": "user", "content": "Urgent CFO-approved transfer now."}],
            provider="openai",
            source=EventSource.CAPTURED,
            psych_context=PsychContext(
                source=PsychContextSource.CAPTURED,
                capture_mode=PsychCaptureMode.HASH_REF,
                snapshot_id="spf_1100",
                convergence_score=0.75,
                artifact_path="psych/000_spf_1100.json",
                artifact_hash=psych_hash,
                psych_root_hash="a" * 64,
                reasoning_root_ref="rt_20260221_1100",
                ui_root_ref="ut_20260221_1100",
            ),
        )
    )
    writer.finalize()

    psych_dir = vault_path / "psych"
    psych_dir.mkdir(parents=True, exist_ok=True)
    (psych_dir / "000_spf_1100.json").write_text(
        json.dumps(psych_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    export_bundle(vault_path, bundle_path)
    return bundle_path


def test_week8_psych_bundle_verifies(tmp_path: Path):
    bundle_path = _make_psych_bundle(tmp_path)
    result = verify_bundle(bundle_path)
    assert result.valid is True


def test_week8_psych_bundle_fails_closed_on_modified_artifact(tmp_path: Path):
    bundle_path = _make_psych_bundle(tmp_path)
    psych_path = bundle_path / "psych" / "000_spf_1100.json"
    payload = json.loads(psych_path.read_text(encoding="utf-8"))
    payload["convergence_score"] = 0.95
    psych_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    result = verify_bundle(bundle_path)
    assert result.valid is False
    assert "Psych artifact psych/000_spf_1100.json: hash mismatch" in result.message


def test_week8_psych_bundle_fails_closed_on_extra_artifact(tmp_path: Path):
    bundle_path = _make_psych_bundle(tmp_path)
    extra_path = bundle_path / "psych" / "999_extra.json"
    extra_path.write_text('{"extra": true}', encoding="utf-8")

    result = verify_bundle(bundle_path)
    assert result.valid is False
    assert "extra psych artifacts" in result.message


def test_week8_report_renders_psych_context_section(tmp_path: Path):
    bundle_path = _make_psych_bundle(tmp_path)
    out_dir = tmp_path / "report"
    report_result = generate_audit_report(bundle_path, out_dir=out_dir)

    report_text = (out_dir / "audit_report.md").read_text(encoding="utf-8")
    assert report_result.psych_context_count == 1
    assert "## Psychological Context (Captured/Referenced)" in report_text
    assert "snapshot_id=spf_1100" in report_text
