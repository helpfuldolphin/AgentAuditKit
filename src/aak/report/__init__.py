"""Deterministic defensible narrative report generation for AAK."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aak.canon.hasher import domain_hash
from aak.replay import ReplayError, ReplayFrame, ReplayTimeline, replay_timeline, verify_bundle

REPORT_VERSION = "0.1.0"
REPORT_FILENAME = "audit_report.md"

REPORT_NON_CLAIMS = (
    "This report is a deterministic summary of recorded events from an AAK evidence bundle. "
    "It does not assert correctness, safety, compliance certification, or governance authority."
)


class ReportError(Exception):
    """Raised when report generation fails."""


@dataclass(frozen=True)
class ReportGenerationResult:
    """Output metadata for a deterministic report run."""

    bundle_id: str
    event_count: int
    decision_point_count: int
    report_hash: str
    output_dir: Path
    report_path: Path


def _load_manifest(bundle_path: Path) -> dict[str, Any]:
    manifest_path = bundle_path / "replay_manifest.json"
    if not manifest_path.exists():
        raise ReportError(f"Missing manifest: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReportError(f"Invalid manifest JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ReportError("Manifest root must be an object")
    return manifest


def _string_or_unknown(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else "UNKNOWN"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return "UNKNOWN"


def _json_or_unknown(value: Any) -> str:
    if not isinstance(value, dict):
        return "UNKNOWN"
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _decision_reason(frame: ReplayFrame) -> str | None:
    payload = frame.payload
    event_type = str(payload.get("event_type", frame.event_type))
    if event_type == "llm_response":
        tool_calls = payload.get("tool_calls")
        if isinstance(tool_calls, list) and len(tool_calls) > 0:
            return "Model output requested a tool invocation"
        return None
    if event_type == "tool_call":
        return "Tool invocation crossed an execution boundary"
    if event_type == "tool_result":
        return "Tool result changed execution state"
    if event_type == "rag_retrieval":
        return "External retrieval context entered decision path"
    return None


def _build_decision_point_lines(timeline: ReplayTimeline) -> list[str]:
    lines: list[str] = []
    for frame in timeline.frames:
        reason = _decision_reason(frame)
        if reason is None:
            continue
        lines.append(
            (
                f"- seq={frame.seq:03d} | event_type={frame.event_type} | reason={reason} | "
                f"payload_file={frame.payload_file} | event_hash={frame.event_hash}"
            )
        )
    if not lines:
        return ["- none"]
    return lines


def _build_tool_and_side_effect_lines(timeline: ReplayTimeline) -> list[str]:
    lines: list[str] = []
    for frame in timeline.frames:
        payload = frame.payload
        event_type = str(payload.get("event_type", frame.event_type))
        if event_type == "tool_call":
            lines.append(
                (
                    f"- seq={frame.seq:03d} | kind=tool_call | "
                    f"tool_name={_string_or_unknown(payload.get('tool_name'))} | "
                    f"triggered_by_seq={_string_or_unknown(payload.get('triggered_by_seq'))} | "
                    f"payload_file={frame.payload_file}"
                )
            )
        elif event_type == "tool_result":
            success = _string_or_unknown(payload.get("success"))
            side_effect = (
                "external-change-candidate" if payload.get("success") is True else "execution-no-op"
            )
            lines.append(
                (
                    f"- seq={frame.seq:03d} | kind=tool_result | "
                    f"tool_name={_string_or_unknown(payload.get('tool_name'))} | "
                    f"success={success} | side_effect={side_effect} | "
                    f"call_seq={_string_or_unknown(payload.get('call_seq'))} | "
                    f"payload_file={frame.payload_file}"
                )
            )
    if not lines:
        return ["- none"]
    return lines


def _build_timeline_lines(timeline: ReplayTimeline) -> list[str]:
    lines: list[str] = []
    for frame in timeline.frames:
        lines.append(
            (
                f"- seq={frame.seq:03d} | timestamp={frame.timestamp} | "
                f"event_type={frame.event_type} | "
                f"payload_file={frame.payload_file} | event_hash={frame.event_hash}"
            )
        )
    if not lines:
        return ["- none"]
    return lines


def _render_report(
    manifest: dict[str, Any],
    timeline: ReplayTimeline,
    verify_message: str,
    decision_lines: list[str],
) -> str:
    metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
    assert isinstance(metadata, dict)

    accountability_requested_by = "UNKNOWN"
    accountability_approved_by = "UNKNOWN"
    accountability_environment = "UNKNOWN"
    accountability_policy_version = "UNKNOWN"
    report_lines = [
        f"# AAK Defensible Narrative Report v{REPORT_VERSION}",
        "",
        f"NON-CLAIMS: {REPORT_NON_CLAIMS}",
        "",
        "## Run Metadata",
        f"- bundle_id: {_string_or_unknown(manifest.get('bundle_id'))}",
        f"- created_at: {_string_or_unknown(manifest.get('created_at'))}",
        f"- event_count: {len(timeline.frames)}",
        f"- chain_root: {_string_or_unknown(manifest.get('chain_root'))}",
        f"- chain_head: {_string_or_unknown(manifest.get('chain_head'))}",
        f"- sdk_version: {_string_or_unknown(metadata.get('sdk_version'))}",
        f"- model_id: {_string_or_unknown(metadata.get('model_id'))}",
        f"- provider: {_string_or_unknown(metadata.get('provider'))}",
        f"- sampling_params: {_json_or_unknown(metadata.get('sampling_params'))}",
        "",
        "## Control And Accountability Fields",
        f"- requested_by: {accountability_requested_by}",
        f"- approved_by: {accountability_approved_by}",
        f"- environment: {accountability_environment}",
        f"- policy_version: {accountability_policy_version}",
        "",
        "## Replay Verification Summary",
        "- verify_status: PASS",
        f"- verify_message: {verify_message}",
        f"- timeline_hash: {timeline.timeline_hash}",
        f"- clock_policy: {timeline.clock_policy}",
        "",
        "## Condensed Timeline",
        *_build_timeline_lines(timeline),
        "",
        "## Decision Points (Rule-Based)",
        *decision_lines,
        "",
        "## Tool Calls And Side Effects",
        *_build_tool_and_side_effect_lines(timeline),
        "",
        "## Explicit Non-Claims",
        "- This report summarizes recorded events only.",
        "- This report does not prove decision correctness or policy compliance.",
        "- This report does not reproduce hosted-LLM outputs deterministically.",
    ]
    return "\n".join(report_lines) + "\n"


def generate_audit_report(
    bundle_path: str | Path,
    *,
    out_dir: str | Path,
) -> ReportGenerationResult:
    """
    Generate deterministic narrative report from a verified bundle.

    Fails closed if bundle verification fails.
    """
    bundle_path_obj = Path(bundle_path)
    verification = verify_bundle(bundle_path_obj)
    if not verification.valid:
        raise ReportError(f"Bundle verification failed: {verification.message}")

    try:
        timeline = replay_timeline(bundle_path_obj)
    except ReplayError as exc:
        raise ReportError(str(exc)) from exc

    manifest = _load_manifest(bundle_path_obj)
    decision_lines = _build_decision_point_lines(timeline)
    decision_point_count = 0 if decision_lines == ["- none"] else len(decision_lines)
    report_text = _render_report(manifest, timeline, verification.message, decision_lines)

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / REPORT_FILENAME
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    report_hash = domain_hash("manifest", {"report_text": report_text})
    return ReportGenerationResult(
        bundle_id=timeline.bundle_id,
        event_count=len(timeline.frames),
        decision_point_count=decision_point_count,
        report_hash=report_hash,
        output_dir=output_dir,
        report_path=report_path,
    )


__all__ = [
    "REPORT_FILENAME",
    "REPORT_NON_CLAIMS",
    "REPORT_VERSION",
    "ReportError",
    "ReportGenerationResult",
    "generate_audit_report",
]
