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

    # Verify hash chain
    prev_hash = GENESIS_HASH
    for i, event_ref in enumerate(events):
        seq = event_ref.get("seq")
        expected_hash = event_ref.get("hash")
        expected_prev = event_ref.get("prev_hash")
        payload_file = event_ref.get("payload_file")

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

        # Update chain
        prev_hash = chain_hash(prev_hash, computed_hash)

    # Verify chain head
    expected_head = manifest.get("chain_head")
    if prev_hash != expected_head:
        return (
            False,
            f"Chain head mismatch: expected {expected_head[:16]}..., got {prev_hash[:16]}...",
            {},
        )

    msg = f"Verification passed. {len(events)} events, chain intact."
    return True, msg, {"event_count": len(events)}


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
