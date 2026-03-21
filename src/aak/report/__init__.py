"""Deterministic exhibit-grade evidence-pack generation for AAK."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aak.canon.hasher import domain_hash
from aak.replay import ReplayError, ReplayFrame, ReplayTimeline, replay_timeline, verify_bundle

REPORT_VERSION = "0.3.0"
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
    decision_context_count: int
    psych_context_count: int
    verifier_evidence_count: int
    report_hash: str
    output_dir: Path
    report_path: Path
    evidence_pack_manifest_path: Path


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


def _string_or_not_recorded(value: Any) -> str:
    if value is None:
        return "not recorded"
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else "not recorded"
    return _string_or_unknown(value)


def _json_or_unknown(value: Any) -> str:
    if not isinstance(value, dict):
        return "UNKNOWN"
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _list_or_none(values: list[str]) -> str:
    if not values:
        return "none"
    return "; ".join(values)


def _short_text(value: Any, *, max_len: int = 96) -> str:
    if not isinstance(value, str):
        return "record not available"
    normalized = " ".join(value.split())
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 3] + "..."


def _message_summary(payload: dict[str, Any]) -> str:
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return "record not available"

    content_parts: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content_parts.append(_short_text(message.get("content")))
    if not content_parts:
        return "record not available"
    return " / ".join(content_parts[:2])


def _decision_context_for_frame(frame: ReplayFrame) -> dict[str, Any] | None:
    decision_context = frame.payload.get("decision_context")
    if isinstance(decision_context, dict):
        return decision_context
    return None


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
        decision_context = _decision_context_for_frame(frame)
        action_summary = "UNKNOWN"
        reversible = "UNKNOWN"
        if decision_context is not None:
            action_summary = _string_or_unknown(decision_context.get("action_summary"))
            reversible = _string_or_unknown(decision_context.get("reversible"))
        lines.append(
            (
                f"- seq={frame.seq:03d} | event_type={frame.event_type} | reason={reason} | "
                f"action_summary={action_summary} | reversible={reversible} | "
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
        decision_context = _decision_context_for_frame(frame)
        reversible = "UNKNOWN"
        if decision_context is not None:
            reversible = _string_or_unknown(decision_context.get("reversible"))
        if event_type == "tool_call":
            lines.append(
                (
                    f"- seq={frame.seq:03d} | kind=tool_call | "
                    f"tool_name={_string_or_unknown(payload.get('tool_name'))} | "
                    f"triggered_by_seq={_string_or_unknown(payload.get('triggered_by_seq'))} | "
                    f"reversible={reversible} | "
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
                    f"reversible={reversible} | "
                    f"call_seq={_string_or_unknown(payload.get('call_seq'))} | "
                    f"payload_file={frame.payload_file}"
                )
            )
    if not lines:
        return ["- none"]
    return lines


def _build_psych_context_lines(timeline: ReplayTimeline) -> list[str]:
    lines: list[str] = []
    for frame in timeline.frames:
        payload = frame.payload
        psych_context = payload.get("psych_context")
        if not isinstance(psych_context, dict):
            continue

        lines.append(
            (
                f"- seq={frame.seq:03d} | "
                f"snapshot_id={_string_or_unknown(psych_context.get('snapshot_id'))} | "
                f"source={_string_or_unknown(psych_context.get('source'))} | "
                f"capture_mode={_string_or_unknown(psych_context.get('capture_mode'))} | "
                f"convergence_score={_string_or_unknown(psych_context.get('convergence_score'))} | "
                f"psych_root_hash={_string_or_unknown(psych_context.get('psych_root_hash'))} | "
                f"artifact_path={_string_or_unknown(psych_context.get('artifact_path'))} | "
                f"artifact_hash={_string_or_unknown(psych_context.get('artifact_hash'))}"
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


def _build_verifier_evidence_lines(manifest: dict[str, Any]) -> list[str]:
    entries = manifest.get("verifier_evidence", [])
    if not isinstance(entries, list) or not entries:
        return ["- none"]

    lines: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        lines.append(
            (
                f"- claim_id={_string_or_unknown(entry.get('claim_id'))} | "
                f"verifier_id={_string_or_unknown(entry.get('verifier_id'))} | "
                f"verifier_kind={_string_or_unknown(entry.get('verifier_kind'))} | "
                f"status={_string_or_unknown(entry.get('status'))} | "
                f"verified_at={_string_or_unknown(entry.get('verified_at'))} | "
                f"proof_hash={_string_or_unknown(entry.get('proof_hash'))} | "
                f"artifact_path={_string_or_unknown(entry.get('artifact_path'))}"
            )
        )
    return lines or ["- none"]


def _build_decision_context_chain(timeline: ReplayTimeline) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    for frame in timeline.frames:
        decision_context = _decision_context_for_frame(frame)
        if decision_context is None:
            continue
        chain.append(
            {
                "seq": frame.seq,
                "timestamp": frame.timestamp,
                "event_type": frame.event_type,
                "payload_file": frame.payload_file,
                "event_hash": frame.event_hash,
                "snapshot_id": decision_context.get("snapshot_id"),
                "requested_by": decision_context.get("requested_by"),
                "approved_by": decision_context.get("approved_by"),
                "environment": decision_context.get("environment"),
                "policy_version": decision_context.get("policy_version"),
                "action_summary": decision_context.get("action_summary"),
                "reversible": decision_context.get("reversible"),
                "perceived_world_state": decision_context.get("perceived_world_state", []),
                "upstream_inputs": decision_context.get("upstream_inputs", []),
                "missing_confidence_signals": decision_context.get(
                    "missing_confidence_signals", []
                ),
                "confidence_signals": decision_context.get("confidence_signals", []),
                "context_references": decision_context.get("context_references", []),
                "counterfactual_checks": decision_context.get("counterfactual_checks", []),
            }
        )
    return chain


def _build_decision_context_lines(chain: list[dict[str, Any]]) -> list[str]:
    if not chain:
        return ["- none"]

    lines: list[str] = []
    for entry in chain:
        snapshot_id = _string_or_unknown(entry.get("snapshot_id"))
        action_summary = _string_or_not_recorded(entry.get("action_summary"))
        requested_by = _string_or_unknown(entry.get("requested_by"))
        approved_by = _string_or_unknown(entry.get("approved_by"))
        policy_version = _string_or_unknown(entry.get("policy_version"))
        reversible = _string_or_unknown(entry.get("reversible"))
        missing_signals = _list_or_none(entry.get("missing_confidence_signals", []))
        context_ref_count = len(entry.get("context_references", []))
        payload_file = _string_or_unknown(entry.get("payload_file"))
        lines.append(
            (
                f"- seq={int(entry['seq']):03d} | snapshot_id={snapshot_id} | "
                f"action_summary={action_summary} | requested_by={requested_by} | "
                f"approved_by={approved_by} | policy_version={policy_version} | "
                f"reversible={reversible} | missing_confidence_signals={missing_signals} | "
                f"context_refs={context_ref_count} | payload_file={payload_file}"
            )
        )
    return lines


def _extract_accountability(
    manifest: dict[str, Any], chain: list[dict[str, Any]]
) -> tuple[str, str, str, str]:
    metadata = manifest.get("metadata")
    accountability: dict[str, Any] = {}
    if isinstance(metadata, dict) and isinstance(metadata.get("accountability"), dict):
        accountability = metadata["accountability"]

    requested_by = accountability.get("requested_by")
    approved_by = accountability.get("approved_by")
    environment = accountability.get("environment")
    policy_version = accountability.get("policy_version")

    for entry in chain:
        if requested_by is None and entry.get("requested_by") is not None:
            requested_by = entry.get("requested_by")
        if approved_by is None and entry.get("approved_by") is not None:
            approved_by = entry.get("approved_by")
        if environment is None and entry.get("environment") is not None:
            environment = entry.get("environment")
        if policy_version is None and entry.get("policy_version") is not None:
            policy_version = entry.get("policy_version")

    return (
        _string_or_unknown(requested_by),
        _string_or_unknown(approved_by),
        _string_or_unknown(environment),
        _string_or_unknown(policy_version),
    )


def _narrative_line(frame: ReplayFrame) -> str:
    payload = frame.payload
    event_type = str(payload.get("event_type", frame.event_type))
    decision_context = _decision_context_for_frame(frame)
    action_summary = "not recorded"
    reversible = "not recorded"
    if decision_context is not None:
        action_summary = _string_or_not_recorded(decision_context.get("action_summary"))
        reversible = _string_or_not_recorded(decision_context.get("reversible"))

    if event_type == "session_start":
        description = "The capture session started."
    elif event_type == "llm_request":
        description = (
            "The agent received a new decision input. "
            f"Message summary: {_message_summary(payload)}."
        )
    elif event_type == "llm_response":
        tool_calls = payload.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            tool_name = "tool"
            first_tool = tool_calls[0]
            if isinstance(first_tool, dict):
                function = first_tool.get("function")
                if isinstance(function, dict):
                    tool_name = _string_or_unknown(function.get("name"))
            description = f"The model requested tool `{tool_name}`."
        else:
            description = (
                "The agent produced a recorded response. "
                f"Response summary: {_short_text(payload.get('content'))}."
            )
    elif event_type == "tool_call":
        description = (
            "The workflow crossed an execution boundary through tool "
            f"`{_string_or_unknown(payload.get('tool_name'))}`."
        )
    elif event_type == "tool_result":
        outcome = "successful result" if payload.get("success") is True else "failure/hold result"
        description = (
            f"Tool `{_string_or_unknown(payload.get('tool_name'))}` returned a {outcome}."
        )
    elif event_type == "rag_retrieval":
        description = "External retrieval context entered the decision path."
    else:
        description = f"Recorded event `{event_type}`."

    context_note = ""
    if decision_context is not None:
        world_state = decision_context.get("perceived_world_state", [])
        if isinstance(world_state, list) and world_state:
            context_note = f" Recorded world state: {_list_or_none(world_state)}."
        missing_signals = decision_context.get("missing_confidence_signals", [])
        if isinstance(missing_signals, list) and missing_signals:
            context_note += (
                " Missing confidence signals: "
                f"{_list_or_none([str(item) for item in missing_signals])}."
            )
        context_note += f" Reversibility: {reversible}."

    return (
        f"- {frame.timestamp}: {description} "
        f"Recorded action summary: {action_summary}.{context_note} "
        f"Evidence: {frame.payload_file}."
    )


def _build_temporal_narrative_lines(timeline: ReplayTimeline) -> list[str]:
    if not timeline.frames:
        return ["- none"]
    return [_narrative_line(frame) for frame in timeline.frames]


def _build_counterfactual_lines(chain: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []

    for entry in chain:
        seq = int(entry["seq"])
        for prompt in entry.get("counterfactual_checks", []):
            if not isinstance(prompt, str):
                continue
            line = f"- seq={seq:03d} | review_check={prompt}"
            if line not in seen:
                lines.append(line)
                seen.add(line)

        missing_signals = entry.get("missing_confidence_signals", [])
        if isinstance(missing_signals, list):
            for signal in missing_signals:
                line = (
                    f"- seq={seq:03d} | review_check=Confirm whether missing confidence signal "
                    f"`{signal}` should have triggered additional review before action."
                )
                if line not in seen:
                    lines.append(line)
                    seen.add(line)

        if entry.get("reversible") is False:
            line = (
                f"- seq={seq:03d} | review_check=Check whether a reversible hold, preview, or "
                "approval checkpoint existed before this irreversible step."
            )
            if line not in seen:
                lines.append(line)
                seen.add(line)

    if not lines:
        return ["- none recorded"]
    return lines


def _build_mermaid_timeline(
    bundle_id: str, timeline: ReplayTimeline, chain: list[dict[str, Any]]
) -> str:
    lines = [
        "flowchart TD",
        f'    title["AAK Decision Timeline: {bundle_id}"]',
    ]

    contexts_by_seq = {int(entry["seq"]): entry for entry in chain}
    previous_node = "title"
    for frame in timeline.frames:
        context = contexts_by_seq.get(frame.seq)
        action_summary = "event recorded"
        if context is not None:
            action_summary = _string_or_not_recorded(context.get("action_summary"))
        label = (
            f"{frame.seq:03d} | {frame.timestamp}<br/>{frame.event_type}<br/>{action_summary}"
        ).replace('"', "'")
        node_name = f"n{frame.seq:03d}"
        lines.append(f'    {node_name}["{label}"]')
        lines.append(f"    {previous_node} --> {node_name}")
        previous_node = node_name

    return "\n".join(lines) + "\n"


def _render_report(
    manifest: dict[str, Any],
    timeline: ReplayTimeline,
    verify_message: str,
    decision_lines: list[str],
    decision_context_lines: list[str],
    psych_lines: list[str],
    temporal_narrative_lines: list[str],
    counterfactual_lines: list[str],
    verifier_evidence_lines: list[str],
) -> str:
    metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
    assert isinstance(metadata, dict)

    (
        accountability_requested_by,
        accountability_approved_by,
        accountability_environment,
        accountability_policy_version,
    ) = _extract_accountability(
        manifest,
        _build_decision_context_chain(timeline),
    )
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
        f"- workflow_id: {_string_or_unknown(metadata.get('workflow_id'))}",
        f"- workflow_name: {_string_or_unknown(metadata.get('workflow_name'))}",
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
        "## Temporal Narrative Summary",
        *temporal_narrative_lines,
        "",
        "## Condensed Timeline",
        *_build_timeline_lines(timeline),
        "",
        "## Decision Points (Rule-Based)",
        *decision_lines,
        "",
        "## Decision Context Chain",
        *decision_context_lines,
        "",
        "## Psychological Context (Captured/Referenced)",
        *psych_lines,
        "",
        "## External Verifier Evidence",
        *verifier_evidence_lines,
        "",
        "## Tool Calls And Side Effects",
        *_build_tool_and_side_effect_lines(timeline),
        "",
        "## Counterfactual Review Checklist",
        *counterfactual_lines,
        "",
        "## Explicit Non-Claims",
        "- This report summarizes recorded events only.",
        "- This report does not prove decision correctness or policy compliance.",
        "- This report does not reproduce hosted-LLM outputs deterministically.",
    ]
    return "\n".join(report_lines) + "\n"


def _render_named_markdown(title: str, body_lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *body_lines]) + "\n"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )


def _copy_bundle(source_bundle: Path, destination_bundle: Path) -> None:
    shutil.copytree(source_bundle, destination_bundle, dirs_exist_ok=True)


def _text_artifact_hash(path: str, content: str) -> str:
    return domain_hash("manifest", {"path": path, "content": content})


def generate_audit_report(
    bundle_path: str | Path,
    *,
    out_dir: str | Path,
) -> ReportGenerationResult:
    """
    Generate deterministic evidence-pack artifacts from a verified bundle.

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
    decision_context_chain = _build_decision_context_chain(timeline)
    decision_context_lines = _build_decision_context_lines(decision_context_chain)
    psych_lines = _build_psych_context_lines(timeline)
    verifier_evidence_lines = _build_verifier_evidence_lines(manifest)
    temporal_narrative_lines = _build_temporal_narrative_lines(timeline)
    counterfactual_lines = _build_counterfactual_lines(decision_context_chain)

    decision_point_count = 0 if decision_lines == ["- none"] else len(decision_lines)
    decision_context_count = len(decision_context_chain)
    psych_context_count = 0 if psych_lines == ["- none"] else len(psych_lines)
    verifier_entries = manifest.get("verifier_evidence", [])
    verifier_evidence_count = len(verifier_entries) if isinstance(verifier_entries, list) else 0
    report_text = _render_report(
        manifest,
        timeline,
        verification.message,
        decision_lines,
        decision_context_lines,
        psych_lines,
        temporal_narrative_lines,
        counterfactual_lines,
        verifier_evidence_lines,
    )
    temporal_narrative_text = _render_named_markdown(
        "Temporal Narrative",
        [
            REPORT_NON_CLAIMS,
            "",
            *temporal_narrative_lines,
        ],
    )
    counterfactual_text = _render_named_markdown(
        "Counterfactual Review Checklist",
        [
            (
                "These are review prompts derived from recorded evidence and explicit "
                "missing evidence."
            ),
            "",
            *counterfactual_lines,
        ],
    )
    mermaid_text = _build_mermaid_timeline(
        timeline.bundle_id,
        timeline,
        decision_context_chain,
    )

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / REPORT_FILENAME
    temporal_narrative_path = output_dir / "temporal_narrative.md"
    counterfactual_path = output_dir / "counterfactual_checklist.md"
    decision_context_chain_path = output_dir / "decision_context_chain.json"
    mermaid_path = output_dir / "decision_timeline.mmd"
    bundle_copy_path = output_dir / "bundle"
    evidence_pack_manifest_path = output_dir / "evidence_pack_manifest.json"

    _write_text(report_path, report_text)
    _write_text(temporal_narrative_path, temporal_narrative_text)
    _write_text(counterfactual_path, counterfactual_text)
    _write_json(
        decision_context_chain_path,
        {
            "bundle_id": timeline.bundle_id,
            "timeline_hash": timeline.timeline_hash,
            "decision_context_count": decision_context_count,
            "contexts": decision_context_chain,
        },
    )
    _write_text(mermaid_path, mermaid_text)
    _copy_bundle(bundle_path_obj, bundle_copy_path)

    report_hash = domain_hash("manifest", {"report_text": report_text})
    generated_files = [
        {
            "path": REPORT_FILENAME,
            "artifact_hash": _text_artifact_hash(REPORT_FILENAME, report_text),
        },
        {
            "path": temporal_narrative_path.name,
            "artifact_hash": _text_artifact_hash(
                temporal_narrative_path.name,
                temporal_narrative_text,
            ),
        },
        {
            "path": counterfactual_path.name,
            "artifact_hash": _text_artifact_hash(counterfactual_path.name, counterfactual_text),
        },
        {
            "path": decision_context_chain_path.name,
            "artifact_hash": domain_hash(
                "manifest",
                {
                    "bundle_id": timeline.bundle_id,
                    "timeline_hash": timeline.timeline_hash,
                    "decision_context_count": decision_context_count,
                    "contexts": decision_context_chain,
                },
            ),
        },
        {
            "path": mermaid_path.name,
            "artifact_hash": _text_artifact_hash(mermaid_path.name, mermaid_text),
        },
    ]
    _write_json(
        evidence_pack_manifest_path,
        {
            "version": REPORT_VERSION,
            "bundle_id": timeline.bundle_id,
            "timeline_hash": timeline.timeline_hash,
            "report_hash": report_hash,
            "decision_point_count": decision_point_count,
            "decision_context_count": decision_context_count,
            "psych_context_count": psych_context_count,
            "verifier_evidence_count": verifier_evidence_count,
            "bundle_copy_path": "bundle",
            "generated_files": generated_files,
        },
    )

    return ReportGenerationResult(
        bundle_id=timeline.bundle_id,
        event_count=len(timeline.frames),
        decision_point_count=decision_point_count,
        decision_context_count=decision_context_count,
        psych_context_count=psych_context_count,
        verifier_evidence_count=verifier_evidence_count,
        report_hash=report_hash,
        output_dir=output_dir,
        report_path=report_path,
        evidence_pack_manifest_path=evidence_pack_manifest_path,
    )


__all__ = [
    "REPORT_FILENAME",
    "REPORT_NON_CLAIMS",
    "REPORT_VERSION",
    "ReportError",
    "ReportGenerationResult",
    "generate_audit_report",
]
