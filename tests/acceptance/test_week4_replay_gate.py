"""Week 4 replay gate tests for deterministic replay core."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from aak.canon.hasher import domain_hash
from aak.models.events import LLMRequestEvent, LLMResponseEvent, SessionStartEvent, ToolCallEvent
from aak.replay import REPLAY_CLOCK_POLICY, ReplayError, replay_timeline, verify_bundle
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


def _make_replay_bundle(tmp_path: Path) -> Path:
    vault_path = tmp_path / "vault"
    bundle_path = tmp_path / "bundle"

    writer = VaultWriter(vault_path)
    writer.append_event(
        SessionStartEvent(run_id=writer.run_id, sdk_version="0.1.0", vault_path=str(vault_path))
    )
    request = LLMRequestEvent(
        model_id="gpt-4",
        messages=[{"role": "user", "content": "please do this immediately"}],
        provider="openai",
    )
    req_envelope = writer.append_event(request)
    writer.append_event(
        LLMResponseEvent(
            model_id="gpt-4",
            content=None,
            tool_calls=[
                {
                    "id": "call_01",
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
    export_bundle(vault_path, bundle_path, include_verify_script=True)
    return bundle_path


def test_replay_timeline_is_deterministic(tmp_path: Path):
    """Same bundle should replay to the same timeline and hash repeatedly."""
    bundle_path = _make_replay_bundle(tmp_path)
    baseline = replay_timeline(bundle_path)

    assert baseline.clock_policy == REPLAY_CLOCK_POLICY

    baseline_dict = baseline.to_dict()
    baseline_hash = baseline.timeline_hash

    for _ in range(100):
        replayed = replay_timeline(bundle_path)
        assert replayed.timeline_hash == baseline_hash
        assert replayed.to_dict() == baseline_dict


def test_replay_verify_fails_on_modified_artifact(tmp_path: Path):
    """Replay verification fails closed when a payload is modified."""
    bundle_path = _make_replay_bundle(tmp_path)
    event_path = sorted((bundle_path / "events").glob("*.json"))[1]
    event_path.write_text(
        event_path.read_text(encoding="utf-8").replace("immediately", "now-now"),
        encoding="utf-8",
    )

    result = verify_bundle(bundle_path)
    assert result.valid is False
    assert "hash mismatch" in result.message.lower()

    with pytest.raises(ReplayError):
        replay_timeline(bundle_path)


def test_replay_verify_fails_on_extra_artifact(tmp_path: Path):
    """Replay verification fails closed when extra artifacts are present."""
    bundle_path = _make_replay_bundle(tmp_path)
    extra = bundle_path / "events" / "999_extra.json"
    extra.write_text(json.dumps({"unexpected": True}), encoding="utf-8")

    result = verify_bundle(bundle_path)
    assert result.valid is False
    assert "extra artifacts" in result.message.lower()

    cli = _run_cli(["replay", "verify", "--bundle", str(bundle_path)])
    assert cli.returncode == 1
    assert "extra artifacts" in cli.stdout.lower()


def test_replay_verify_fails_on_missing_artifact(tmp_path: Path):
    """Replay verification fails closed when referenced artifacts are missing."""
    bundle_path = _make_replay_bundle(tmp_path)
    event_path = sorted((bundle_path / "events").glob("*.json"))[1]
    event_path.unlink()

    result = verify_bundle(bundle_path)
    assert result.valid is False
    assert "missing artifacts" in result.message.lower()
