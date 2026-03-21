#!/usr/bin/env python3
"""
Standalone verification script for Agent Audit Kit bundles.
This file is copied into exported bundles.

IMPORTANT: This script uses the SAME canonicalization and hashing
logic as the main SDK. The code is embedded at export time.

Usage:
    python verify.py

Exit codes:
    0 - Verification passed
    1 - Verification failed (tampering detected)
    2 - Error (missing files, etc.)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# === EMBEDDED RFC 8785 CANONICALIZATION ===
# This is the SAME code as src/aak/canon/rfc8785.py

def _encode_string(s):
    """Encode string with minimal escape sequences per RFC 8785."""
    result = ['"']
    for char in s:
        code = ord(char)
        if char == '"':
            result.append('\\"')
        elif char == "\\":
            result.append("\\\\")
        elif code < 0x20:
            if char == "\b":
                result.append("\\b")
            elif char == "\f":
                result.append("\\f")
            elif char == "\n":
                result.append("\\n")
            elif char == "\r":
                result.append("\\r")
            elif char == "\t":
                result.append("\\t")
            else:
                result.append(f"\\u{code:04x}")
        else:
            result.append(char)
    result.append('"')
    return "".join(result)


def _encode_number(n):
    """Encode number per RFC 8785."""
    import math
    if isinstance(n, bool):
        return "true" if n else "false"
    if isinstance(n, int):
        return str(n)
    if math.isnan(n) or math.isinf(n):
        return "null"
    if n == 0.0:
        return "0"
    s = repr(n)
    s = s.replace("E", "e").replace("e+", "e")
    return s


def canonicalize(obj):
    """RFC 8785 canonical JSON serialization."""
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, str):
        return _encode_string(obj)
    if isinstance(obj, (int, float)):
        return _encode_number(obj)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        sorted_keys = sorted(obj.keys(), key=lambda k: [ord(c) for c in str(k)])
        pairs = [f"{_encode_string(str(k))}:{canonicalize(obj[k])}" for k in sorted_keys]
        return "{" + ",".join(pairs) + "}"
    if isinstance(obj, (list, tuple)):
        if not obj:
            return "[]"
        elements = [canonicalize(v) for v in obj]
        return "[" + ",".join(elements) + "]"
    return _encode_string(str(obj))


# === EMBEDDED DOMAIN-SEPARATED HASHING ===
# This is the SAME code as src/aak/canon/hasher.py

import hashlib

DOMAINS = {
    "event": b"aak:v0:event:",
    "chain": b"aak:v0:chain:",
    "manifest": b"aak:v0:manifest:",
}

GENESIS_HASH = hashlib.sha256(b"aak:v0:genesis").hexdigest()


def domain_hash(domain, data):
    """Domain-separated SHA256 hash."""
    if domain not in DOMAINS:
        raise ValueError(f"Unknown domain: {domain}")
    prefix = DOMAINS[domain]
    if isinstance(data, bytes):
        payload = data
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, dict):
        payload = canonicalize(data).encode("utf-8")
    else:
        payload = canonicalize(data).encode("utf-8")
    return hashlib.sha256(prefix + payload).hexdigest()


def chain_hash(prev_hash, event_hash):
    """Compute hash chain link."""
    payload = f"{prev_hash}:{event_hash}".encode("utf-8")
    return hashlib.sha256(DOMAINS["chain"] + payload).hexdigest()



def _is_safe_rel_path(rel_path: str, root_dir: str) -> bool:
    path = Path(rel_path)
    if path.is_absolute():
        return False
    if ".." in path.parts:
        return False
    return path.parts[:1] == (root_dir,)


def _collect_inventory(bundle_path: Path, directory: str) -> set[str]:
    target = bundle_path / directory
    if not target.exists():
        return set()
    if not target.is_dir():
        raise ValueError(f"{directory} path is not a directory: {target}")

    inventory = set()
    for path in target.rglob("*"):
        if path.is_file():
            inventory.add(path.relative_to(bundle_path).as_posix())
    return inventory


def verify_bundle(bundle_path: Path) -> tuple[bool, str, dict]:
    """
    Verify bundle integrity.

    Returns:
        (success, message, details)
    """
    manifest_path = bundle_path / "replay_manifest.json"
    events_dir = bundle_path / "events"

    if not manifest_path.exists():
        return False, "Missing replay_manifest.json", {}
    if not events_dir.exists():
        return False, "Missing events directory", {}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"Invalid manifest JSON: {e}", {}

    events = manifest.get("events", [])
    if not events:
        return False, "No events in manifest", {}

    declared_event_files = set()
    declared_psych_artifacts = {}
    declared_verifier_artifacts = {}

    verifier_evidence_entries = manifest.get("verifier_evidence", [])
    if verifier_evidence_entries is None:
        verifier_evidence_entries = []
    if not isinstance(verifier_evidence_entries, list):
        return False, "Manifest field verifier_evidence must be an array", {}
    for entry in verifier_evidence_entries:
        if not isinstance(entry, dict):
            return False, "Verifier evidence entry must be an object", {}
        artifact_path = entry.get("artifact_path")
        artifact_hash = entry.get("artifact_hash")
        if artifact_path is None and artifact_hash is None:
            continue
        if not isinstance(artifact_path, str) or not isinstance(artifact_hash, str):
            return False, "Verifier evidence artifact fields must be strings", {}
        if not _is_safe_rel_path(artifact_path, "verifiers"):
            return False, f"Invalid verifier artifact path: {artifact_path}", {}
        previous = declared_verifier_artifacts.get(artifact_path)
        if previous is not None and previous != artifact_hash:
            return False, f"Conflicting verifier artifact hash for {artifact_path}", {}
        declared_verifier_artifacts[artifact_path] = artifact_hash

    # Verify hash chain
    prev_hash = GENESIS_HASH
    for event_ref in events:
        seq = event_ref.get("seq")
        expected_hash = event_ref.get("hash")
        expected_prev = event_ref.get("prev_hash")
        payload_file = event_ref.get("payload_file")

        if not isinstance(payload_file, str) or not _is_safe_rel_path(payload_file, "events"):
            return False, f"Event {seq}: invalid payload_file path", {"seq": seq}
        declared_event_files.add(payload_file)

        # Check prev_hash linkage
        if expected_prev != prev_hash:
            return False, f"Event {seq}: prev_hash mismatch (chain broken)", {"seq": seq}

        # Load and hash event payload
        event_path = bundle_path / payload_file
        if not event_path.exists():
            return False, f"Event {seq}: missing payload file {payload_file}", {"seq": seq}

        try:
            event_data = json.loads(event_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return False, f"Event {seq}: invalid JSON: {e}", {"seq": seq}

        computed_hash = domain_hash("event", event_data)
        if computed_hash != expected_hash:
            return False, f"Event {seq}: hash mismatch (tampering detected)", {"seq": seq}

        psych_context = event_data.get("psych_context")
        if psych_context is not None:
            if not isinstance(psych_context, dict):
                return False, f"Event {seq}: psych_context must be an object", {"seq": seq}

            artifact_path = psych_context.get("artifact_path")
            artifact_hash = psych_context.get("artifact_hash")
            if artifact_path is None and artifact_hash is None:
                pass
            elif not isinstance(artifact_path, str) or not isinstance(artifact_hash, str):
                return (
                    False,
                    f"Event {seq}: psych_context artifact fields must be strings",
                    {"seq": seq},
                )
            elif not _is_safe_rel_path(artifact_path, "psych"):
                return False, f"Event {seq}: invalid psych artifact path", {"seq": seq}
            else:
                previous = declared_psych_artifacts.get(artifact_path)
                if previous is not None and previous != artifact_hash:
                    return (
                        False,
                        f"Event {seq}: conflicting psych artifact hash for {artifact_path}",
                        {"seq": seq},
                    )
                declared_psych_artifacts[artifact_path] = artifact_hash

        # Update chain
        prev_hash = chain_hash(prev_hash, computed_hash)

    actual_event_files = _collect_inventory(bundle_path, "events")
    extra_event_files = sorted(actual_event_files - declared_event_files)
    missing_event_files = sorted(declared_event_files - actual_event_files)
    if extra_event_files or missing_event_files:
        parts = []
        if extra_event_files:
            parts.append(f"extra event artifacts: {', '.join(extra_event_files)}")
        if missing_event_files:
            parts.append(f"missing event artifacts: {', '.join(missing_event_files)}")
        return False, "; ".join(parts), {}

    # Verify chain head
    expected_head = manifest.get("chain_head")
    if prev_hash != expected_head:
        return (
            False,
            f"Chain head mismatch: expected {expected_head[:16]}..., got {prev_hash[:16]}...",
            {},
        )

    declared_psych_files = set(declared_psych_artifacts.keys())
    actual_psych_files = _collect_inventory(bundle_path, "psych")
    extra_psych_files = sorted(actual_psych_files - declared_psych_files)
    missing_psych_files = sorted(declared_psych_files - actual_psych_files)
    if extra_psych_files or missing_psych_files:
        parts = []
        if extra_psych_files:
            parts.append(f"extra psych artifacts: {', '.join(extra_psych_files)}")
        if missing_psych_files:
            parts.append(f"missing psych artifacts: {', '.join(missing_psych_files)}")
        return False, "; ".join(parts), {}

    for artifact_path, expected_hash in sorted(declared_psych_artifacts.items()):
        artifact_full_path = bundle_path / artifact_path
        try:
            artifact_payload = json.loads(artifact_full_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, f"Psych artifact {artifact_path}: invalid JSON ({exc})", {}

        computed_hash = domain_hash("manifest", artifact_payload)
        if computed_hash != expected_hash:
            return False, f"Psych artifact {artifact_path}: hash mismatch", {}

    declared_verifier_files = set(declared_verifier_artifacts.keys())
    actual_verifier_files = _collect_inventory(bundle_path, "verifiers")
    extra_verifier_files = sorted(actual_verifier_files - declared_verifier_files)
    missing_verifier_files = sorted(declared_verifier_files - actual_verifier_files)
    if extra_verifier_files or missing_verifier_files:
        parts = []
        if extra_verifier_files:
            parts.append(f"extra verifier artifacts: {', '.join(extra_verifier_files)}")
        if missing_verifier_files:
            parts.append(f"missing verifier artifacts: {', '.join(missing_verifier_files)}")
        return False, "; ".join(parts), {}

    for artifact_path, expected_hash in sorted(declared_verifier_artifacts.items()):
        artifact_full_path = bundle_path / artifact_path
        try:
            artifact_payload = json.loads(artifact_full_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, f"Verifier artifact {artifact_path}: invalid JSON ({exc})", {}

        computed_hash = domain_hash("manifest", artifact_payload)
        if computed_hash != expected_hash:
            return False, f"Verifier artifact {artifact_path}: hash mismatch", {}

    msg = (
        "Verification passed. "
        f"{len(events)} events, {len(declared_psych_artifacts)} psych artifacts, "
        f"{len(declared_verifier_artifacts)} verifier artifacts, chain intact."
    )
    return True, msg, {
        "event_count": len(events),
        "psych_artifact_count": len(declared_psych_artifacts),
        "verifier_artifact_count": len(declared_verifier_artifacts),
    }


def main() -> None:
    bundle_path = Path(__file__).parent

    print("=" * 60)
    print(" AGENT AUDIT KIT - Evidence Bundle Verification")
    print("=" * 60)
    print()

    manifest_path = bundle_path / "replay_manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            print(f" Bundle ID:    {manifest.get('bundle_id', 'unknown')}")
            print(f" Created:      {manifest.get('created_at', 'unknown')}")
            print(f" Event Count:  {manifest.get('event_count', 0)}")
            print()
        except json.JSONDecodeError:
            pass

    success, message, details = verify_bundle(bundle_path)

    if success:
        print(" Hash Chain:   [OK] INTACT")
        print(" Manifest:     [OK] VALID")
        print()

        # Show threat flags if present
        flags = manifest.get("threat_flags", [])
        if flags:
            print(" THREAT FLAGS:")
            for flag in flags:
                severity = flag.get("severity", "UNKNOWN")
                threat_class = flag.get("threat_class", "UNKNOWN")
                tags = ", ".join(flag.get("owasp_asi_tags", []))
                desc = flag.get("description", "")[:60]
                print(f"   [{severity}] {threat_class}: {tags}")
                print(f"           {desc}...")
            print()

        print(" Status: EVIDENCE ARTIFACT GENERATED")
        print("         (Not a compliance certification)")
        print()
        print("=" * 60)
        sys.exit(0)
    else:
        print(" Hash Chain:   [FAIL] INVALID")
        print(f" Error:        {message}")
        print()
        print(" Status: VERIFICATION FAILED")
        print()
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
