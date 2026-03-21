"""Bundle export functionality."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from aak import __version__
from aak.canon.hasher import EMBEDDED_HASHER, domain_hash
from aak.canon.rfc8785 import EMBEDDED_CANONICALIZE
from aak.models.manifest import ReplayManifest, SessionMetadata
from aak.models.psych import PsychCaptureMode, PsychContextSource
from aak.models.threats import ThreatFlag
from aak.models.verifier import VerifierEvidence
from aak.vault.store import VaultReader


@dataclass
class ExportResult:
    """Result of bundle export."""

    bundle_path: Path
    manifest_hash: str
    event_count: int
    threat_flags_count: int
    verifier_evidence_count: int


def _copy_optional_directory(vault_path: Path, output_path: Path, directory: str) -> int:
    source_root = vault_path / directory
    if not source_root.exists():
        return 0
    if not source_root.is_dir():
        raise ValueError(f"{directory} artifact path is not a directory: {source_root}")

    copied_count = 0
    for source_path in source_root.rglob("*"):
        if not source_path.is_file():
            continue
        relative_path = source_path.relative_to(vault_path)
        destination = output_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        copied_count += 1
    return copied_count


def _summarize_psych_context(
    events_source: Path,
) -> tuple[bool, PsychCaptureMode | None, PsychContextSource | None]:
    enabled = False
    capture_mode: PsychCaptureMode | None = None
    context_source: PsychContextSource | None = None

    for event_file in sorted(events_source.glob("*.json")):
        payload = json.loads(event_file.read_text(encoding="utf-8"))
        psych_context = payload.get("psych_context")
        if not isinstance(psych_context, dict):
            continue

        enabled = True
        if capture_mode is None:
            mode_value = psych_context.get("capture_mode")
            if isinstance(mode_value, str):
                try:
                    capture_mode = PsychCaptureMode(mode_value)
                except ValueError:
                    capture_mode = None
        if context_source is None:
            source_value = psych_context.get("source")
            if isinstance(source_value, str):
                try:
                    context_source = PsychContextSource(source_value)
                except ValueError:
                    context_source = None

    return enabled, capture_mode, context_source


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
        raise ValueError(f"{{directory}} path is not a directory: {{target}}")

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

    declared_event_files = set()
    declared_psych_artifacts = {{}}
    declared_verifier_artifacts = {{}}

    verifier_evidence_entries = manifest.get("verifier_evidence", [])
    if verifier_evidence_entries is None:
        verifier_evidence_entries = []
    if not isinstance(verifier_evidence_entries, list):
        return False, "Manifest field verifier_evidence must be an array", {{}}
    for entry in verifier_evidence_entries:
        if not isinstance(entry, dict):
            return False, "Verifier evidence entry must be an object", {{}}
        artifact_path = entry.get("artifact_path")
        artifact_hash = entry.get("artifact_hash")
        if artifact_path is None and artifact_hash is None:
            continue
        if not isinstance(artifact_path, str) or not isinstance(artifact_hash, str):
            return False, "Verifier evidence artifact fields must be strings", {{}}
        if not _is_safe_rel_path(artifact_path, "verifiers"):
            return False, f"Invalid verifier artifact path: {{artifact_path}}", {{}}
        previous = declared_verifier_artifacts.get(artifact_path)
        if previous is not None and previous != artifact_hash:
            return False, f"Conflicting verifier artifact hash for {{artifact_path}}", {{}}
        declared_verifier_artifacts[artifact_path] = artifact_hash

    # Verify hash chain
    prev_hash = GENESIS_HASH
    for event_ref in events:
        seq = event_ref.get("seq")
        expected_hash = event_ref.get("hash")
        expected_prev = event_ref.get("prev_hash")
        payload_file = event_ref.get("payload_file")

        if not isinstance(payload_file, str) or not _is_safe_rel_path(payload_file, "events"):
            return False, f"Event {{seq}}: invalid payload_file path", {{"seq": seq}}
        declared_event_files.add(payload_file)

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

        psych_context = event_data.get("psych_context")
        if psych_context is not None:
            if not isinstance(psych_context, dict):
                return False, f"Event {{seq}}: psych_context must be an object", {{"seq": seq}}

            artifact_path = psych_context.get("artifact_path")
            artifact_hash = psych_context.get("artifact_hash")
            if artifact_path is None and artifact_hash is None:
                pass
            elif not isinstance(artifact_path, str) or not isinstance(artifact_hash, str):
                return (
                    False,
                    f"Event {{seq}}: psych_context artifact fields must be strings",
                    {{"seq": seq}},
                )
            elif not _is_safe_rel_path(artifact_path, "psych"):
                return False, f"Event {{seq}}: invalid psych artifact path", {{"seq": seq}}
            else:
                previous = declared_psych_artifacts.get(artifact_path)
                if previous is not None and previous != artifact_hash:
                    return (
                        False,
                        f"Event {{seq}}: conflicting psych artifact hash for {{artifact_path}}",
                        {{"seq": seq}},
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
            parts.append(f"extra event artifacts: {{', '.join(extra_event_files)}}")
        if missing_event_files:
            parts.append(f"missing event artifacts: {{', '.join(missing_event_files)}}")
        return False, "; ".join(parts), {{}}

    # Verify chain head
    expected_head = manifest.get("chain_head")
    if prev_hash != expected_head:
        return (
            False,
            f"Chain head mismatch: expected {{expected_head[:16]}}..., got {{prev_hash[:16]}}...",
            {{}},
        )

    declared_psych_files = set(declared_psych_artifacts.keys())
    actual_psych_files = _collect_inventory(bundle_path, "psych")
    extra_psych_files = sorted(actual_psych_files - declared_psych_files)
    missing_psych_files = sorted(declared_psych_files - actual_psych_files)
    if extra_psych_files or missing_psych_files:
        parts = []
        if extra_psych_files:
            parts.append(f"extra psych artifacts: {{', '.join(extra_psych_files)}}")
        if missing_psych_files:
            parts.append(f"missing psych artifacts: {{', '.join(missing_psych_files)}}")
        return False, "; ".join(parts), {{}}

    for artifact_path, expected_hash in sorted(declared_psych_artifacts.items()):
        artifact_full_path = bundle_path / artifact_path
        try:
            artifact_payload = json.loads(artifact_full_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, f"Psych artifact {{artifact_path}}: invalid JSON ({{exc}})", {{}}

        computed_hash = domain_hash("manifest", artifact_payload)
        if computed_hash != expected_hash:
            return False, f"Psych artifact {{artifact_path}}: hash mismatch", {{}}

    declared_verifier_files = set(declared_verifier_artifacts.keys())
    actual_verifier_files = _collect_inventory(bundle_path, "verifiers")
    extra_verifier_files = sorted(actual_verifier_files - declared_verifier_files)
    missing_verifier_files = sorted(declared_verifier_files - actual_verifier_files)
    if extra_verifier_files or missing_verifier_files:
        parts = []
        if extra_verifier_files:
            parts.append(f"extra verifier artifacts: {{', '.join(extra_verifier_files)}}")
        if missing_verifier_files:
            parts.append(f"missing verifier artifacts: {{', '.join(missing_verifier_files)}}")
        return False, "; ".join(parts), {{}}

    for artifact_path, expected_hash in sorted(declared_verifier_artifacts.items()):
        artifact_full_path = bundle_path / artifact_path
        try:
            artifact_payload = json.loads(artifact_full_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, f"Verifier artifact {{artifact_path}}: invalid JSON ({{exc}})", {{}}

        computed_hash = domain_hash("manifest", artifact_payload)
        if computed_hash != expected_hash:
            return False, f"Verifier artifact {{artifact_path}}: hash mismatch", {{}}

    msg = (
        "Verification passed. "
        f"{{len(events)}} events, {{len(declared_psych_artifacts)}} psych artifacts, "
        f"{{len(declared_verifier_artifacts)}} verifier artifacts, chain intact."
    )
    return True, msg, {{
        "event_count": len(events),
        "psych_artifact_count": len(declared_psych_artifacts),
        "verifier_artifact_count": len(declared_verifier_artifacts),
    }}


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
    session_metadata: SessionMetadata | None = None,
    verifier_evidence: list[VerifierEvidence] | None = None,
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

    psych_enabled, detected_mode, detected_source = _summarize_psych_context(events_source)
    copied_psych_artifacts = _copy_optional_directory(vault_path, output_path, "psych")
    copied_verifier_artifacts = _copy_optional_directory(vault_path, output_path, "verifiers")
    if copied_psych_artifacts > 0:
        psych_enabled = True

    metadata = session_metadata or SessionMetadata(sdk_version=__version__)
    if psych_enabled:
        metadata = metadata.model_copy(
            update={
                "psych_context_enabled": True,
                "psych_contract_version": (
                    metadata.psych_contract_version or "CPF_CONTEXT_CONTRACT_V0_2"
                ),
                "psych_capture_mode": (
                    metadata.psych_capture_mode or detected_mode or PsychCaptureMode.HASH_REF
                ),
                "psych_source": (
                    metadata.psych_source or detected_source or PsychContextSource.CAPTURED
                ),
            }
        )
    if verifier_evidence:
        metadata = metadata.model_copy(
            update={
                "verifier_contract_version": metadata.verifier_contract_version
                or "VERIFIER_EVIDENCE_CONTRACT_V0_3"
            }
        )

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

    created_at = envelopes[0].timestamp if envelopes else datetime.now(timezone.utc)

    manifest = ReplayManifest(
        bundle_id=run_id,
        created_at=created_at,
        chain_root=verification.chain_root,
        chain_head=verification.chain_head,
        events=[e.model_dump(mode="json") for e in envelopes],
        event_count=verification.event_count,
        metadata=metadata,
        threat_flags=threat_flags or [],
        verifier_evidence=verifier_evidence or [],
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
Psych:     {copied_psych_artifacts} artifact(s)
Verifiers: {copied_verifier_artifacts} artifact(s)

VERIFICATION
------------
Run: python verify.py

This will verify:
- hash chain integrity of all events
- optional psych artifact references and hashes
- optional verifier artifact references and hashes

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
        verifier_evidence_count=len(verifier_evidence or []),
    )
