"""Week 2 CLI gate tests for command surface and exit codes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from aak.canon.hasher import domain_hash
from aak.models.events import LLMRequestEvent, ToolCallEvent
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
        LLMRequestEvent(
            model_id="gpt-4",
            messages=[{"role": "user", "content": "please do this immediately"}],
            provider="openai",
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


def test_cli_help_includes_non_claims():
    """Top-level help should include non-claims language."""
    result = _run_cli(["--help"])
    assert result.returncode == 0
    assert "does not provide compliance certification" in result.stdout.lower()


def test_cli_missing_command_returns_exit_2():
    """Missing command should return deterministic usage exit code."""
    result = _run_cli([])
    assert result.returncode == 2


def test_replay_verify_exit_codes(tmp_path: Path):
    """Replay verify returns 0 on intact bundles and 1 on tampered bundles."""
    bundle_path = _make_bundle(tmp_path)

    intact = _run_cli(["replay", "verify", "--bundle", str(bundle_path)])
    assert intact.returncode == 0
    assert "[OK]" in intact.stdout

    event_path = sorted((bundle_path / "events").glob("*.json"))[0]
    data = event_path.read_text(encoding="utf-8")
    event_path.write_text(data.replace("immediately", "now-now"), encoding="utf-8")

    tampered = _run_cli(["replay", "verify", "--bundle", str(bundle_path)])
    assert tampered.returncode == 1
    assert "[FAIL]" in tampered.stdout


def test_stress_run_authority_profile(tmp_path: Path):
    """Stress run should produce deterministic report artifact."""
    bundle_path = _make_bundle(tmp_path)

    result = _run_cli(
        ["stress", "run", "--bundle", str(bundle_path), "--profile", "authority", "--seed", "7"]
    )
    assert result.returncode == 0

    stress_dir = bundle_path / "stress_runs" / "authority"
    run_path = stress_dir / "stress_run.json"
    diff_path = stress_dir / "stress_diff.json"
    assert run_path.exists()
    assert diff_path.exists()

    run_manifest = json.loads(run_path.read_text(encoding="utf-8"))
    diff_manifest = json.loads(diff_path.read_text(encoding="utf-8"))
    assert run_manifest["profile"] == "authority"
    assert run_manifest["seed"] == 7
    assert run_manifest["finding_count"] >= 1
    assert "run_hash" in run_manifest
    assert diff_manifest["profile"] == "authority"
    assert diff_manifest["change_count"] == 0
    assert "diff_hash" in diff_manifest


def test_capture_run_creates_bundle_and_verifies(tmp_path: Path):
    """Capture run should create a bundle that replay verify accepts."""
    output_dir = tmp_path / "capture_output"
    config_path = tmp_path / "aak.yaml"
    config_path.write_text("runtime: declared\n", encoding="utf-8")

    capture = _run_cli(["capture", "run", "--config", str(config_path), "--out", str(output_dir)])
    assert capture.returncode == 0
    assert (output_dir / "bundle" / "replay_manifest.json").exists()

    verify = _run_cli(["replay", "verify", "--bundle", str(output_dir / "bundle")])
    assert verify.returncode == 0
