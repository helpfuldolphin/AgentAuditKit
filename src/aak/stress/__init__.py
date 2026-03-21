"""Deterministic stress runner for AAK v0.1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aak.canon.hasher import domain_hash
from aak.replay import ReplayError, replay_timeline

STRESS_VERSION = "0.3.0"
STRESS_PROFILE_AUTHORITY = "authority"
SUPPORTED_STRESS_PROFILES = (STRESS_PROFILE_AUTHORITY,)
DIFF_DETERMINISM_MODE = "strict-identical"

NON_CLAIMS = (
    "AAK stress artifacts are evidence for investigation. They do not provide compliance "
    "certification, governance authority, or deterministic hosted-LLM output reproduction."
)

_PRIVILEGED_TOOL_TERMS = ("ssn", "admin", "root", "delete", "shutdown", "pii")


class StressError(Exception):
    """Raised when stress execution fails."""


@dataclass(frozen=True)
class StressRunResult:
    """Deterministic stress execution result."""

    profile: str
    bundle_id: str
    seed: int
    finding_count: int
    run_hash: str
    diff_hash: str
    output_dir: Path
    run_manifest_path: Path
    diff_path: Path


def _extract_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_extract_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_extract_text(v) for v in value.values())
    return ""


def _build_authority_findings(timeline_payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for seq, payload in enumerate(timeline_payloads):
        event_type = str(payload.get("event_type", "unknown"))
        tool_name = str(payload.get("tool_name", "")).lower()
        if any(term in tool_name for term in _PRIVILEGED_TOOL_TERMS):
            findings.append(
                {
                    "seq": seq,
                    "event_type": event_type,
                    "severity": "HIGH",
                    "reason": f"Privileged tool pattern in '{tool_name}'",
                    "evidence_hash": domain_hash("event", payload),
                }
            )
    findings.sort(key=lambda finding: (int(finding["seq"]), str(finding["reason"])))
    return findings


def _serialize_json_deterministic(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_stress(
    bundle_path: str | Path,
    *,
    profile: str,
    seed: int,
    output_dir: str | Path | None = None,
) -> StressRunResult:
    """
    Run deterministic stress profile on a verified bundle.

    For v0.1, only `authority` profile is supported in the release gate.
    """
    if profile not in SUPPORTED_STRESS_PROFILES:
        raise StressError(
            f"Unsupported profile '{profile}'. Supported: {', '.join(SUPPORTED_STRESS_PROFILES)}"
        )

    try:
        timeline = replay_timeline(bundle_path)
    except ReplayError as exc:
        raise StressError(str(exc)) from exc

    payloads = [frame.payload for frame in timeline.frames]
    findings = _build_authority_findings(payloads)

    diff_payload = {
        "version": STRESS_VERSION,
        "profile": profile,
        "bundle_id": timeline.bundle_id,
        "determinism_mode": DIFF_DETERMINISM_MODE,
        "baseline_timeline_hash": timeline.timeline_hash,
        "stressed_timeline_hash": timeline.timeline_hash,
        "change_count": 0,
        "changes": [],
    }
    diff_hash = domain_hash("manifest", diff_payload)
    diff_artifact = {**diff_payload, "diff_hash": diff_hash}

    run_payload = {
        "version": STRESS_VERSION,
        "profile": profile,
        "bundle_id": timeline.bundle_id,
        "seed": seed,
        "finding_count": len(findings),
        "findings": findings,
        "baseline_timeline_hash": timeline.timeline_hash,
        "diff_hash": diff_hash,
        "non_claims": NON_CLAIMS,
    }
    run_hash = domain_hash("manifest", run_payload)
    run_manifest = {**run_payload, "run_hash": run_hash}

    if output_dir is None:
        out_dir = Path(bundle_path) / "stress_runs" / profile
    else:
        out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_manifest_path = out_dir / "stress_run.json"
    diff_path = out_dir / "stress_diff.json"
    _serialize_json_deterministic(run_manifest_path, run_manifest)
    _serialize_json_deterministic(diff_path, diff_artifact)

    return StressRunResult(
        profile=profile,
        bundle_id=timeline.bundle_id,
        seed=seed,
        finding_count=len(findings),
        run_hash=run_hash,
        diff_hash=diff_hash,
        output_dir=out_dir,
        run_manifest_path=run_manifest_path,
        diff_path=diff_path,
    )


__all__ = [
    "DIFF_DETERMINISM_MODE",
    "STRESS_PROFILE_AUTHORITY",
    "SUPPORTED_STRESS_PROFILES",
    "StressError",
    "StressRunResult",
    "run_stress",
]
