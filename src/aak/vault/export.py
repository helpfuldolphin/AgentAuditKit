"""Bundle export functionality."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from aak.canon.hasher import EMBEDDED_HASHER, domain_hash
from aak.canon.rfc8785 import EMBEDDED_CANONICALIZE
from aak.models.manifest import ReplayManifest, SessionMetadata
from aak.models.threats import ThreatFlag
from aak.vault.store import VaultReader


@dataclass
class ExportResult:
    """Result of bundle export."""

    bundle_path: Path
    manifest_hash: str
    event_count: int
    threat_flags_count: int


def _generate_verify_script() -> str:
    """
    Generate verify.py with embedded canonicalization and hashing code.

    This ensures verify.py uses the EXACT same logic as src/aak/canon/.
    """
    return f'''#!/usr/bin/env python3
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
{EMBEDDED_CANONICALIZE}

# === EMBEDDED DOMAIN-SEPARATED HASHING ===
# This is the SAME code as src/aak/canon/hasher.py
{EMBEDDED_HASHER}


def verify_bundle(bundle_path: Path) -> tuple[bool, str, dict]:
    """
    Verify bundle integrity.

    Returns:
        (success, message, details)
    """
    manifest_path = bundle_path / "replay_manifest.json"
    events_dir = bundle_path / "events"

    if not manifest_path.exists():
        return False, "Missing replay_manifest.json", {{}}
    if not events_dir.exists():
        return False, "Missing events directory", {{}}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"Invalid manifest JSON: {{e}}", {{}}

    events = manifest.get("events", [])
    if not events:
        return False, "No events in manifest", {{}}

    # Verify hash chain
    prev_hash = GENESIS_HASH
    for i, event_ref in enumerate(events):
        seq = event_ref.get("seq")
        expected_hash = event_ref.get("hash")
        expected_prev = event_ref.get("prev_hash")
        payload_file = event_ref.get("payload_file")

        # Check prev_hash linkage
        if expected_prev != prev_hash:
            return False, f"Event {{seq}}: prev_hash mismatch (chain broken)", {{"seq": seq}}

        # Load and hash event payload
        event_path = bundle_path / payload_file
        if not event_path.exists():
            return False, f"Event {{seq}}: missing payload file {{payload_file}}", {{"seq": seq}}

        try:
            event_data = json.loads(event_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return False, f"Event {{seq}}: invalid JSON: {{e}}", {{"seq": seq}}

        computed_hash = domain_hash("event", event_data)
        if computed_hash != expected_hash:
            return False, f"Event {{seq}}: hash mismatch (tampering detected)", {{"seq": seq}}

        # Update chain
        prev_hash = chain_hash(prev_hash, computed_hash)

    # Verify chain head
    expected_head = manifest.get("chain_head")
    if prev_hash != expected_head:
        return (
            False,
            f"Chain head mismatch: expected {{expected_head[:16]}}..., got {{prev_hash[:16]}}...",
            {{}},
        )

    msg = f"Verification passed. {{len(events)}} events, chain intact."
    return True, msg, {{"event_count": len(events)}}


def main() -> None:
    bundle_path = Path(__file__).parent

    print("=" * 60)
    print(" AGENT AUDIT KIT - Evidence Bundle Verification")
    print("=" * 60)
    print()

    manifest_path = bundle_path / "replay_manifest.json"
    manifest = {{}}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            print(f" Bundle ID:    {{manifest.get('bundle_id', 'unknown')}}")
            print(f" Created:      {{manifest.get('created_at', 'unknown')}}")
            print(f" Event Count:  {{manifest.get('event_count', 0)}}")
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
                print(f"   [{{severity}}] {{threat_class}}: {{tags}}")
                print(f"           {{desc}}...")
            print()

        print(" Status: EVIDENCE ARTIFACT GENERATED")
        print("         (Not a compliance certification)")
        print()
        print("=" * 60)
        sys.exit(0)
    else:
        print(" Hash Chain:   [FAIL] INVALID")
        print(f" Error:        {{message}}")
        print()
        print(" Status: VERIFICATION FAILED")
        print()
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
'''


def export_bundle(
    vault_path: str | Path,
    output_path: str | Path,
    *,
    include_verify_script: bool = True,
    threat_flags: list[ThreatFlag] | None = None,
) -> ExportResult:
    """
    Export vault to portable, self-contained bundle.

    Creates:
        output_path/
        ├── replay_manifest.json
        ├── events/
        │   ├── 000_session_start.json
        │   ├── 001_llm_request.json
        │   └── ...
        ├── verify.py           (if include_verify_script)
        └── README.txt

    Returns:
        ExportResult with bundle_path, manifest_hash, event_count.
    """
    vault_path = Path(vault_path)
    output_path = Path(output_path)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    events_output = output_path / "events"
    events_output.mkdir(exist_ok=True)

    # Read vault
    reader = VaultReader(vault_path)
    verification = reader.verify_chain()

    if not verification.valid:
        raise ValueError(f"Cannot export invalid vault: {verification.error_message}")

    # Copy event files
    events_source = vault_path / "events"
    for event_file in sorted(events_source.glob("*.json")):
        shutil.copy2(event_file, events_output / event_file.name)

    # Build manifest
    envelopes = list(reader.iter_events())

    # Extract run_id from chain log if available
    chain_log_path = vault_path / "chain.log"
    run_id = "run_unknown"
    if chain_log_path.exists():
        try:
            chain_data = json.loads(chain_log_path.read_text(encoding="utf-8"))
            run_id = chain_data.get("run_id", run_id)
        except (json.JSONDecodeError, KeyError):
            pass

    manifest = ReplayManifest(
        bundle_id=run_id,
        created_at=datetime.now(timezone.utc),
        chain_root=verification.chain_root,
        chain_head=verification.chain_head,
        events=[e.model_dump(mode="json") for e in envelopes],  # type: ignore
        event_count=verification.event_count,
        metadata=SessionMetadata(sdk_version="0.1.0"),
        threat_flags=threat_flags or [],
    )

    # Write manifest (pretty-printed for readability)
    manifest_path = output_path / "replay_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )
    manifest_hash = domain_hash("manifest", manifest.model_dump(mode="json"))

    # Write verify.py
    if include_verify_script:
        verify_script = _generate_verify_script()
        verify_path = output_path / "verify.py"
        verify_path.write_text(verify_script, encoding="utf-8")

    # Write README
    readme = output_path / "README.txt"
    readme.write_text(
        f"""AGENT AUDIT KIT - Evidence Bundle
==================================

Bundle ID: {run_id}
Created:   {manifest.created_at.isoformat()}
Events:    {verification.event_count}

VERIFICATION
------------
Run: python verify.py

This will verify the hash chain integrity of all events.

DISCLAIMER
----------
{manifest.disclaimer}

For more information, see: https://github.com/your-org/agent-audit-kit
""",
        encoding="utf-8",
    )

    return ExportResult(
        bundle_path=output_path,
        manifest_hash=manifest_hash,
        event_count=verification.event_count,
        threat_flags_count=len(threat_flags or []),
    )
