"""Deterministic replay and bundle verification for AAK."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aak.canon.hasher import GENESIS_HASH, chain_hash, domain_hash
from aak.models.psych import psych_artifact_hash

REPLAY_CLOCK_POLICY = "seq_asc_then_manifest_timestamp"

_REQUIRED_MANIFEST_FIELDS = {
    "version",
    "bundle_id",
    "created_at",
    "chain_root",
    "chain_head",
    "events",
    "event_count",
    "metadata",
    "threat_flags",
    "disclaimer",
}

_REQUIRED_ENVELOPE_FIELDS = {"seq", "event_type", "hash", "prev_hash", "timestamp", "payload_file"}


class ReplayError(Exception):
    """Raised when replay processing fails."""


@dataclass(frozen=True)
class ReplayVerificationResult:
    """Verification result for a replay bundle."""

    valid: bool
    message: str
    event_count: int
    bundle_id: str | None = None
    first_invalid_seq: int | None = None


@dataclass(frozen=True)
class ReplayFrame:
    """A single deterministic replay frame."""

    clock_tick: int
    seq: int
    event_type: str
    timestamp: str
    event_hash: str
    prev_hash: str
    payload_file: str
    payload_hash: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize frame deterministically."""
        return {
            "clock_tick": self.clock_tick,
            "seq": self.seq,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "event_hash": self.event_hash,
            "prev_hash": self.prev_hash,
            "payload_file": self.payload_file,
            "payload_hash": self.payload_hash,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class ReplayTimeline:
    """Deterministic replay timeline derived from a verified bundle."""

    version: str
    bundle_id: str
    clock_policy: str
    event_count: int
    chain_root: str
    chain_head: str
    timeline_hash: str
    frames: tuple[ReplayFrame, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize timeline deterministically."""
        return {
            "version": self.version,
            "bundle_id": self.bundle_id,
            "clock_policy": self.clock_policy,
            "event_count": self.event_count,
            "chain_root": self.chain_root,
            "chain_head": self.chain_head,
            "timeline_hash": self.timeline_hash,
            "frames": [frame.to_dict() for frame in self.frames],
        }


def _is_safe_payload_path(payload_file: str) -> bool:
    path = Path(payload_file)
    if path.is_absolute():
        return False
    if ".." in path.parts:
        return False
    return path.parts[:1] == ("events",)


def _is_safe_psych_path(artifact_path: str) -> bool:
    path = Path(artifact_path)
    if path.is_absolute():
        return False
    if ".." in path.parts:
        return False
    return path.parts[:1] == ("psych",)


def _load_manifest(bundle_path: Path) -> dict[str, Any]:
    manifest_path = bundle_path / "replay_manifest.json"
    if not manifest_path.exists():
        raise ReplayError(f"Missing manifest: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReplayError(f"Invalid manifest JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ReplayError("Manifest root must be an object")
    return manifest


def _validate_manifest_shape(manifest: dict[str, Any]) -> None:
    missing_fields = sorted(_REQUIRED_MANIFEST_FIELDS - set(manifest.keys()))
    if missing_fields:
        raise ReplayError(f"Manifest missing required fields: {', '.join(missing_fields)}")
    if not isinstance(manifest.get("events"), list):
        raise ReplayError("Manifest field 'events' must be an array")
    if not isinstance(manifest.get("event_count"), int):
        raise ReplayError("Manifest field 'event_count' must be an integer")


def _collect_events_inventory(events_dir: Path) -> set[str]:
    if not events_dir.exists():
        raise ReplayError(f"Missing events directory: {events_dir}")
    if not events_dir.is_dir():
        raise ReplayError(f"Events path is not a directory: {events_dir}")
    return {f"events/{entry.name}" for entry in events_dir.iterdir() if entry.is_file()}


def _collect_optional_inventory(bundle_path: Path, directory: str) -> set[str]:
    target_dir = bundle_path / directory
    if not target_dir.exists():
        return set()
    if not target_dir.is_dir():
        raise ReplayError(f"{directory} path is not a directory: {target_dir}")

    inventory: set[str] = set()
    for entry in target_dir.rglob("*"):
        if entry.is_file():
            inventory.add(entry.relative_to(bundle_path).as_posix())
    return inventory


def _normalize_and_validate_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for envelope in events:
        if not isinstance(envelope, dict):
            raise ReplayError("Event envelope must be an object")
        missing_fields = sorted(_REQUIRED_ENVELOPE_FIELDS - set(envelope.keys()))
        if missing_fields:
            raise ReplayError(f"Event envelope missing fields: {', '.join(missing_fields)}")
        seq = envelope.get("seq")
        if not isinstance(seq, int) or seq < 0:
            raise ReplayError("Envelope 'seq' must be a non-negative integer")
        payload_file = envelope.get("payload_file")
        if not isinstance(payload_file, str) or not _is_safe_payload_path(payload_file):
            raise ReplayError(f"Invalid payload_file path: {payload_file}")
        normalized.append(envelope)

    normalized.sort(key=lambda e: int(e["seq"]))

    for expected_seq, envelope in enumerate(normalized):
        if int(envelope["seq"]) != expected_seq:
            raise ReplayError(
                "Envelope sequence must be contiguous starting at 0 "
                f"(expected {expected_seq}, got {envelope['seq']})"
            )
    return normalized


def _verify_and_collect(
    bundle_path: Path, *, include_payloads: bool
) -> tuple[
    ReplayVerificationResult,
    dict[str, Any] | None,
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    try:
        manifest = _load_manifest(bundle_path)
        _validate_manifest_shape(manifest)
        bundle_id = manifest.get("bundle_id")
        if not isinstance(bundle_id, str):
            raise ReplayError("Manifest field 'bundle_id' must be a string")

        events = manifest["events"]
        if not isinstance(events, list):
            raise ReplayError("Manifest field 'events' must be an array")
        if manifest["event_count"] != len(events):
            raise ReplayError(
                "Manifest event_count mismatch "
                f"(expected {manifest['event_count']}, found {len(events)})"
            )

        events_dir = bundle_path / "events"
        actual_event_files = _collect_events_inventory(events_dir)

        normalized_events = _normalize_and_validate_events(events)
        declared_event_files = {str(e["payload_file"]) for e in normalized_events}

        extra_files = sorted(actual_event_files - declared_event_files)
        missing_files = sorted(declared_event_files - actual_event_files)
        if extra_files or missing_files:
            message_parts = []
            if extra_files:
                message_parts.append(f"extra artifacts: {', '.join(extra_files)}")
            if missing_files:
                message_parts.append(f"missing artifacts: {', '.join(missing_files)}")
            raise ReplayError("; ".join(message_parts))

        frames_payloads: list[dict[str, Any]] = []
        declared_psych_artifacts: dict[str, str] = {}
        prev_hash = GENESIS_HASH
        chain_root = GENESIS_HASH

        for envelope in normalized_events:
            seq = int(envelope["seq"])
            payload_path = bundle_path / str(envelope["payload_file"])
            try:
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ReplayError(f"Event {seq}: invalid payload JSON ({exc})") from exc

            if not isinstance(payload, dict):
                raise ReplayError(f"Event {seq}: payload must be a JSON object")

            computed_hash = domain_hash("event", payload)
            expected_hash = str(envelope["hash"])
            if computed_hash != expected_hash:
                raise ReplayError(f"Event {seq}: hash mismatch")

            expected_prev = str(envelope["prev_hash"])
            if expected_prev != prev_hash:
                raise ReplayError(f"Event {seq}: prev_hash mismatch")

            if seq == 0:
                chain_root = computed_hash

            psych_context = payload.get("psych_context")
            if psych_context is not None:
                if not isinstance(psych_context, dict):
                    raise ReplayError(f"Event {seq}: psych_context must be an object")
                artifact_path = psych_context.get("artifact_path")
                artifact_hash = psych_context.get("artifact_hash")
                if artifact_path is None and artifact_hash is None:
                    pass
                elif not isinstance(artifact_path, str) or not isinstance(artifact_hash, str):
                    raise ReplayError(
                        f"Event {seq}: psych_context artifact_path/artifact_hash must be strings"
                    )
                elif not _is_safe_psych_path(artifact_path):
                    raise ReplayError(f"Event {seq}: invalid psych artifact_path: {artifact_path}")
                else:
                    existing_hash = declared_psych_artifacts.get(artifact_path)
                    if existing_hash is not None and existing_hash != artifact_hash:
                        raise ReplayError(
                            f"Event {seq}: conflicting psych artifact hash for {artifact_path}"
                        )
                    declared_psych_artifacts[artifact_path] = artifact_hash

            prev_hash = chain_hash(prev_hash, computed_hash)
            if include_payloads:
                frames_payloads.append(payload)

        expected_chain_head = str(manifest["chain_head"])
        if prev_hash != expected_chain_head:
            raise ReplayError("Chain head mismatch")

        expected_chain_root = str(manifest["chain_root"])
        if chain_root != expected_chain_root:
            raise ReplayError("Chain root mismatch")

        actual_psych_files = _collect_optional_inventory(bundle_path, "psych")
        declared_psych_files = set(declared_psych_artifacts.keys())

        extra_psych_files = sorted(actual_psych_files - declared_psych_files)
        missing_psych_files = sorted(declared_psych_files - actual_psych_files)
        if extra_psych_files or missing_psych_files:
            message_parts = []
            if extra_psych_files:
                message_parts.append(f"extra psych artifacts: {', '.join(extra_psych_files)}")
            if missing_psych_files:
                message_parts.append(f"missing psych artifacts: {', '.join(missing_psych_files)}")
            raise ReplayError("; ".join(message_parts))

        for artifact_path, expected_hash in sorted(declared_psych_artifacts.items()):
            artifact_full_path = bundle_path / artifact_path
            try:
                artifact_payload = json.loads(artifact_full_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ReplayError(f"Psych artifact {artifact_path}: invalid JSON ({exc})") from exc

            computed_artifact_hash = psych_artifact_hash(artifact_payload)
            if computed_artifact_hash != expected_hash:
                raise ReplayError(f"Psych artifact {artifact_path}: hash mismatch")

        return (
            ReplayVerificationResult(
                valid=True,
                message=f"Verified {len(normalized_events)} events",
                event_count=len(normalized_events),
                bundle_id=bundle_id,
            ),
            manifest,
            normalized_events,
            frames_payloads,
        )
    except ReplayError as exc:
        return (
            ReplayVerificationResult(
                valid=False,
                message=str(exc),
                event_count=0,
            ),
            None,
            [],
            [],
        )


def verify_bundle(bundle_path: str | Path) -> ReplayVerificationResult:
    """Fail-closed verification for replay bundles."""
    result, _manifest, _events, _payloads = _verify_and_collect(
        Path(bundle_path), include_payloads=False
    )
    return result


def replay_timeline(bundle_path: str | Path) -> ReplayTimeline:
    """
    Build deterministic replay timeline from a verified bundle.

    The replay clock is fixed by sequence order then manifest timestamp.
    """
    result, manifest, events, payloads = _verify_and_collect(
        Path(bundle_path), include_payloads=True
    )
    if not result.valid or manifest is None:
        raise ReplayError(result.message)

    frames: list[ReplayFrame] = []
    for clock_tick, (envelope, payload) in enumerate(zip(events, payloads, strict=True)):
        payload_hash = domain_hash("event", payload)
        frames.append(
            ReplayFrame(
                clock_tick=clock_tick,
                seq=int(envelope["seq"]),
                event_type=str(envelope["event_type"]),
                timestamp=str(envelope["timestamp"]),
                event_hash=str(envelope["hash"]),
                prev_hash=str(envelope["prev_hash"]),
                payload_file=str(envelope["payload_file"]),
                payload_hash=payload_hash,
                payload=payload,
            )
        )

    timeline_payload = {
        "version": str(manifest["version"]),
        "bundle_id": str(manifest["bundle_id"]),
        "clock_policy": REPLAY_CLOCK_POLICY,
        "event_count": len(frames),
        "chain_root": str(manifest["chain_root"]),
        "chain_head": str(manifest["chain_head"]),
        "frames": [frame.to_dict() for frame in frames],
    }
    timeline_hash = domain_hash("manifest", timeline_payload)

    return ReplayTimeline(
        version=str(manifest["version"]),
        bundle_id=str(manifest["bundle_id"]),
        clock_policy=REPLAY_CLOCK_POLICY,
        event_count=len(frames),
        chain_root=str(manifest["chain_root"]),
        chain_head=str(manifest["chain_head"]),
        timeline_hash=timeline_hash,
        frames=tuple(frames),
    )


__all__ = [
    "REPLAY_CLOCK_POLICY",
    "ReplayError",
    "ReplayFrame",
    "ReplayTimeline",
    "ReplayVerificationResult",
    "replay_timeline",
    "verify_bundle",
]
