"""Acceptance tests for exhibit-grade lineage and evidence-pack outputs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _run_cli(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    src_path = str(repo_root / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else src_path
    )
    return subprocess.run(
        [sys.executable, "-m", "aak.cli", *args],
        cwd=str(cwd or repo_root),
        env=env,
        capture_output=True,
        text=True,
    )


def test_week9_capture_run_emits_real_banking_workflow(tmp_path: Path):
    """Capture CLI should emit a real multi-event banking workflow bundle."""
    output_dir = tmp_path / "capture_output"
    config_path = tmp_path / "banking_capture.yaml"
    config_path.write_text(
        "\n".join(
            [
                "scenario: banking_decision_exposure",
                "workflow_id: wire_review_test",
                "workflow_name: Wire Review Test Workflow",
                "requested_by: treasury_queue_alpha",
                "approved_by: dual_control_officer",
                "environment: bank-prod-sim",
                "policy_version: wire_policy_v9",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    capture = _run_cli(["capture", "run", "--config", str(config_path), "--out", str(output_dir)])
    assert capture.returncode == 0
    assert "Workflow: wire_review_test" in capture.stdout

    bundle_path = output_dir / "bundle"
    verify = _run_cli(["replay", "verify", "--bundle", str(bundle_path)])
    assert verify.returncode == 0

    manifest = json.loads((bundle_path / "replay_manifest.json").read_text(encoding="utf-8"))
    assert manifest["event_count"] >= 10
    assert manifest["metadata"]["workflow_id"] == "wire_review_test"
    assert manifest["metadata"]["accountability"]["requested_by"] == "treasury_queue_alpha"
    assert manifest["metadata"]["accountability"]["approved_by"] == "dual_control_officer"

    decision_context_events = []
    for event_path in sorted((bundle_path / "events").glob("*.json")):
        payload = json.loads(event_path.read_text(encoding="utf-8"))
        if payload.get("decision_context") is not None:
            decision_context_events.append(payload)
    assert len(decision_context_events) >= 4


def test_week9_report_generate_emits_evidence_pack(tmp_path: Path):
    """Report generation should create an exhibit-grade evidence pack."""
    output_dir = tmp_path / "capture_output"
    config_path = tmp_path / "banking_capture.yaml"
    config_path.write_text(
        "\n".join(
            [
                "scenario: banking_decision_exposure",
                "workflow_id: wire_review_pack",
                "workflow_name: Wire Review Pack Workflow",
                "requested_by: treasury_queue_beta",
                "approved_by: dual_control_board",
                "environment: bank-stage-sim",
                "policy_version: wire_policy_v10",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    capture = _run_cli(["capture", "run", "--config", str(config_path), "--out", str(output_dir)])
    assert capture.returncode == 0

    bundle_path = output_dir / "bundle"
    report_out = tmp_path / "evidence_pack"
    report = _run_cli(
        ["report", "generate", "--bundle", str(bundle_path), "--out", str(report_out)]
    )
    assert report.returncode == 0
    assert "Decision contexts:" in report.stdout
    assert "Evidence pack manifest:" in report.stdout

    audit_report = (report_out / "audit_report.md").read_text(encoding="utf-8")
    temporal_narrative = (report_out / "temporal_narrative.md").read_text(encoding="utf-8")
    counterfactual = (report_out / "counterfactual_checklist.md").read_text(encoding="utf-8")
    mermaid = (report_out / "decision_timeline.mmd").read_text(encoding="utf-8")
    chain = json.loads((report_out / "decision_context_chain.json").read_text(encoding="utf-8"))
    pack_manifest = json.loads(
        (report_out / "evidence_pack_manifest.json").read_text(encoding="utf-8")
    )

    assert "requested_by: treasury_queue_beta" in audit_report
    assert "approved_by: dual_control_board" in audit_report
    assert "policy_version: wire_policy_v10" in audit_report
    assert "## Decision Context Chain" in audit_report
    assert "## Counterfactual Review Checklist" in audit_report
    assert "AAK Decision Timeline" in mermaid
    assert "Temporal Narrative" in temporal_narrative
    assert "review prompts derived from recorded evidence" in counterfactual
    assert chain["decision_context_count"] >= 4
    assert pack_manifest["decision_context_count"] >= 4
    assert (report_out / "bundle" / "replay_manifest.json").exists()
