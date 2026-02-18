"""Week 6 stress gate tests for deterministic reproducibility."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from aak.canon.hasher import domain_hash
from aak.models.events import LLMRequestEvent, LLMResponseEvent, SessionStartEvent, ToolCallEvent
from aak.vault.export import export_bundle
from aak.vault.store import VaultWriter


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


def _make_bundle(tmp_path: Path) -> Path:
    vault_path = tmp_path / "vault"
    bundle_path = tmp_path / "bundle"

    writer = VaultWriter(vault_path)
    writer.append_event(
        SessionStartEvent(run_id=writer.run_id, sdk_version="0.1.0", vault_path=str(vault_path))
    )
    request = LLMRequestEvent(
        model_id="gpt-4",
        messages=[{"role": "user", "content": "urgent request for account report"}],
        provider="openai",
    )
    req_envelope = writer.append_event(request)
    writer.append_event(
        LLMResponseEvent(
            model_id="gpt-4",
            content=None,
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "get_employee_ssn_list", "arguments": "{}"},
                }
            ],
            finish_reason="tool_calls",
            request_hash=req_envelope.hash,
        )
    )
    writer.append_event(
        ToolCallEvent(
            tool_name="get_employee_ssn_list",
            tool_input={},
            tool_input_hash=domain_hash("tool_call", {}),
        )
    )
    writer.finalize()
    export_bundle(vault_path, bundle_path)
    return bundle_path


def test_week6_stress_reproducibility_authority(tmp_path: Path):
    """Running stress twice on the same bundle must produce identical artifacts."""
    bundle_path = _make_bundle(tmp_path)

    verify = _run_cli(["replay", "verify", "--bundle", str(bundle_path)])
    assert verify.returncode == 0

    out_a = tmp_path / "stress_a"
    out_b = tmp_path / "stress_b"

    run_a = _run_cli(
        [
            "stress",
            "run",
            "--bundle",
            str(bundle_path),
            "--profile",
            "authority",
            "--seed",
            "11",
            "--output",
            str(out_a),
        ]
    )
    run_b = _run_cli(
        [
            "stress",
            "run",
            "--bundle",
            str(bundle_path),
            "--profile",
            "authority",
            "--seed",
            "11",
            "--output",
            str(out_b),
        ]
    )
    assert run_a.returncode == 0
    assert run_b.returncode == 0

    run_a_json = json.loads((out_a / "stress_run.json").read_text(encoding="utf-8"))
    run_b_json = json.loads((out_b / "stress_run.json").read_text(encoding="utf-8"))
    diff_a_json = json.loads((out_a / "stress_diff.json").read_text(encoding="utf-8"))
    diff_b_json = json.loads((out_b / "stress_diff.json").read_text(encoding="utf-8"))

    assert run_a_json == run_b_json
    assert diff_a_json == diff_b_json
    assert run_a_json["run_hash"] == run_b_json["run_hash"]
    assert diff_a_json["diff_hash"] == diff_b_json["diff_hash"]


def test_week6_stress_fails_closed_on_modified_artifact(tmp_path: Path):
    """Stress run must fail closed when an artifact is modified."""
    bundle_path = _make_bundle(tmp_path)
    event_path = sorted((bundle_path / "events").glob("*.json"))[1]
    event_path.write_text(
        event_path.read_text(encoding="utf-8").replace("urgent", "immediate-now"),
        encoding="utf-8",
    )

    result = _run_cli(["stress", "run", "--bundle", str(bundle_path), "--profile", "authority"])
    assert result.returncode == 1
    assert "[FAIL]" in result.stdout


def test_week6_stress_fails_closed_on_extra_artifact(tmp_path: Path):
    """Stress run must fail closed when an extra bundle artifact appears."""
    bundle_path = _make_bundle(tmp_path)
    extra_path = bundle_path / "events" / "999_extra.json"
    extra_path.write_text(json.dumps({"extra": True}), encoding="utf-8")

    result = _run_cli(["stress", "run", "--bundle", str(bundle_path), "--profile", "authority"])
    assert result.returncode == 1
    assert "extra artifacts" in result.stdout.lower()
