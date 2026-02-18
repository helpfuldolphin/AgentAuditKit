"""Week 7 report gate tests for deterministic audit narrative artifacts."""

from __future__ import annotations

import json
import os
import shutil
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


def _golden_bundle_path() -> Path:
    return Path(__file__).resolve().parents[2] / "golden_runs" / "aak-v0.1.0-e3" / "bundle"


def test_week7_report_generation_is_byte_identical(tmp_path: Path):
    """Report generation on the same bundle must produce byte-identical output."""
    bundle_path = _golden_bundle_path()
    out_a = tmp_path / "report_a"
    out_b = tmp_path / "report_b"

    run_a = _run_cli(["report", "generate", "--bundle", str(bundle_path), "--out", str(out_a)])
    run_b = _run_cli(["report", "generate", "--bundle", str(bundle_path), "--out", str(out_b)])

    assert run_a.returncode == 0
    assert run_b.returncode == 0

    report_a = out_a / "audit_report.md"
    report_b = out_b / "audit_report.md"
    bytes_a = report_a.read_bytes()
    bytes_b = report_b.read_bytes()
    assert bytes_a == bytes_b

    text = bytes_a.decode("utf-8")
    assert "NON-CLAIMS" in text
    assert "## Decision Points (Rule-Based)" in text
    assert "requested_by: UNKNOWN" in text


def test_week7_report_fails_closed_on_tampered_bundle(tmp_path: Path):
    """Report generation must fail when a bundle event is modified."""
    source_bundle = _golden_bundle_path()
    tampered_bundle = tmp_path / "tampered_bundle"
    shutil.copytree(source_bundle, tampered_bundle)

    event_path = sorted((tampered_bundle / "events").glob("*.json"))[0]
    payload = json.loads(event_path.read_text(encoding="utf-8"))
    payload["tampered"] = True
    event_path.write_text(json.dumps(payload), encoding="utf-8")

    out_dir = tmp_path / "report_out"
    result = _run_cli(
        ["report", "generate", "--bundle", str(tampered_bundle), "--out", str(out_dir)]
    )
    assert result.returncode == 1
    assert "[FAIL]" in result.stdout
    assert not (out_dir / "audit_report.md").exists()
