"""Immutable vault storage with hash chaining."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from aak.canon.hasher import GENESIS_HASH, chain_hash, domain_hash
from aak.canon.rfc8785 import canonicalize
from aak.models.events import EventBase, EventEnvelope, EventType


class VaultSealedError(Exception):
    """Raised when attempting to write to a sealed vault."""

    pass


class VaultNotFoundError(Exception):
    """Raised when vault directory does not exist."""

    pass


@dataclass
class ChainVerificationResult:
    """Result of hash chain verification."""

    valid: bool
    event_count: int
    chain_root: str
    chain_head: str
    first_invalid_seq: int | None = None
    error_message: str | None = None


class VaultWriter:
    """
    Append-only event store with hash chaining.

    Events are stored as individual JSON files in the events/ directory.
    The hash chain links each event to its predecessor.
    """

    def __init__(self, vault_path: str | Path, *, run_id: str | None = None) -> None:
        self._vault_path = Path(vault_path)
        self._events_path = self._vault_path / "events"
        self._run_id = run_id or f"run_{secrets.token_hex(8)}"
        self._seq = 0
        self._prev_hash = GENESIS_HASH
        self._chain_root: str | None = None
        self._sealed = False
        self._envelopes: list[EventEnvelope] = []

        # Create directories
        self._vault_path.mkdir(parents=True, exist_ok=True)
        self._events_path.mkdir(exist_ok=True)

        # Create lock file
        self._lock_path = self._vault_path / ".lock"
        self._lock_path.touch()

    @property
    def run_id(self) -> str:
        """Current capture session ID."""
        return self._run_id

    @property
    def chain_head(self) -> str:
        """SHA256 hash of most recent chain link."""
        return self._prev_hash

    def append_event(self, event: EventBase) -> EventEnvelope:
        """
        Append event to vault.

        The event_hash is computed over the canonical JSON of the event payload,
        EXCLUDING envelope fields (seq, hash, prev_hash, payload_file).

        Returns:
            EventEnvelope with sequence number, hash, prev_hash, timestamp.

        Raises:
            VaultSealedError: If vault has been finalized.
        """
        if self._sealed:
            raise VaultSealedError("Vault has been finalized. No further writes allowed.")

        # Serialize event payload (this is what gets hashed)
        payload_dict = event.model_dump(mode="json")
        payload_json = canonicalize(payload_dict)

        # Compute event hash (domain-separated)
        event_hash = domain_hash("event", payload_dict)

        # Record chain root (first event)
        if self._chain_root is None:
            self._chain_root = event_hash

        # Create envelope
        event_type_name = event.event_type.value
        payload_file = f"events/{self._seq:03d}_{event_type_name}.json"
        envelope = EventEnvelope(
            seq=self._seq,
            event_type=event.event_type,
            hash=event_hash,
            prev_hash=self._prev_hash,
            timestamp=event.timestamp,
            payload_file=payload_file,
        )

        # Write event file
        event_file = self._vault_path / payload_file
        event_file.write_text(payload_json, encoding="utf-8")

        # Update chain
        self._prev_hash = chain_hash(self._prev_hash, event_hash)
        self._seq += 1
        self._envelopes.append(envelope)

        return envelope

    def finalize(self) -> str:
        """
        Seal the vault. No further writes allowed.

        Returns:
            Final chain head hash.
        """
        if self._sealed:
            return self._prev_hash

        self._sealed = True

        # Write chain log
        chain_log = self._vault_path / "chain.log"
        chain_data = {
            "run_id": self._run_id,
            "event_count": len(self._envelopes),
            "chain_root": self._chain_root or GENESIS_HASH,
            "chain_head": self._prev_hash,
            "envelopes": [e.model_dump(mode="json") for e in self._envelopes],
        }
        chain_log.write_text(json.dumps(chain_data, indent=2, default=str), encoding="utf-8")

        # Remove lock file
        if self._lock_path.exists():
            try:
                self._lock_path.unlink()
            except OSError:
                # Lock cleanup is best-effort; sealed chain state is already persisted.
                pass

        return self._prev_hash

    def get_envelopes(self) -> list[EventEnvelope]:
        """Get all event envelopes."""
        return list(self._envelopes)


class VaultReader:
    """Read-only access to vault (sealed or not)."""

    def __init__(self, vault_path: str | Path) -> None:
        self._vault_path = Path(vault_path)
        if not self._vault_path.exists():
            raise VaultNotFoundError(f"Vault not found: {vault_path}")

        self._events_path = self._vault_path / "events"
        self._chain_log_path = self._vault_path / "chain.log"
        self._envelopes: list[EventEnvelope] | None = None

    def _load_envelopes(self) -> list[EventEnvelope]:
        """Load envelopes from chain log."""
        if self._envelopes is not None:
            return self._envelopes

        if not self._chain_log_path.exists():
            # Try to reconstruct from event files
            self._envelopes = self._reconstruct_envelopes()
        else:
            chain_data = json.loads(self._chain_log_path.read_text(encoding="utf-8"))
            self._envelopes = [EventEnvelope.model_validate(e) for e in chain_data["envelopes"]]

        return self._envelopes

    def _reconstruct_envelopes(self) -> list[EventEnvelope]:
        """Reconstruct envelopes from event files (for verification)."""
        if not self._events_path.exists():
            return []

        envelopes = []
        event_files = sorted(self._events_path.glob("*.json"))
        prev_hash = GENESIS_HASH

        for event_file in event_files:
            # Parse sequence and type from filename
            parts = event_file.stem.split("_", 1)
            seq = int(parts[0])
            event_type_str = parts[1] if len(parts) > 1 else "unknown"

            # Load and hash event
            payload = json.loads(event_file.read_text(encoding="utf-8"))
            event_hash = domain_hash("event", payload)

            # Map string to EventType
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                event_type = EventType.SESSION_START  # fallback

            envelope = EventEnvelope(
                seq=seq,
                event_type=event_type,
                hash=event_hash,
                prev_hash=prev_hash,
                timestamp=datetime.fromisoformat(
                    payload.get("timestamp", datetime.now(timezone.utc).isoformat())
                ),
                payload_file=f"events/{event_file.name}",
            )
            envelopes.append(envelope)
            prev_hash = chain_hash(prev_hash, event_hash)

        return envelopes

    def verify_chain(self) -> ChainVerificationResult:
        """
        Verify hash chain integrity.

        Returns:
            ChainVerificationResult with validity status.
        """
        if not self._events_path.exists():
            return ChainVerificationResult(
                valid=False,
                event_count=0,
                chain_root=GENESIS_HASH,
                chain_head=GENESIS_HASH,
                error_message="Events directory not found",
            )

        event_files = sorted(self._events_path.glob("*.json"))
        if not event_files:
            return ChainVerificationResult(
                valid=True,
                event_count=0,
                chain_root=GENESIS_HASH,
                chain_head=GENESIS_HASH,
            )

        prev_hash = GENESIS_HASH
        chain_root: str | None = None
        event_count = 0

        for event_file in event_files:
            try:
                # Load event payload
                payload_text = event_file.read_text(encoding="utf-8")
                payload = json.loads(payload_text)
            except FileNotFoundError:
                return ChainVerificationResult(
                    valid=False,
                    event_count=event_count,
                    chain_root=chain_root or GENESIS_HASH,
                    chain_head=prev_hash,
                    first_invalid_seq=event_count,
                    error_message=f"Missing event file: {event_file.name}",
                )
            except json.JSONDecodeError as e:
                return ChainVerificationResult(
                    valid=False,
                    event_count=event_count,
                    chain_root=chain_root or GENESIS_HASH,
                    chain_head=prev_hash,
                    first_invalid_seq=event_count,
                    error_message=f"Invalid JSON in {event_file.name}: {e}",
                )

            # Compute expected hash
            computed_hash = domain_hash("event", payload)

            # Record chain root
            if chain_root is None:
                chain_root = computed_hash

            # Update chain
            prev_hash = chain_hash(prev_hash, computed_hash)
            event_count += 1

        # If we have a chain log, verify against it
        if self._chain_log_path.exists():
            try:
                chain_data = json.loads(self._chain_log_path.read_text(encoding="utf-8"))
                expected_head = chain_data.get("chain_head")
                if expected_head and expected_head != prev_hash:
                    return ChainVerificationResult(
                        valid=False,
                        event_count=event_count,
                        chain_root=chain_root or GENESIS_HASH,
                        chain_head=prev_hash,
                        error_message=(
                            f"Chain head mismatch: expected {expected_head[:16]}..., "
                            f"got {prev_hash[:16]}..."
                        ),
                    )
            except (json.JSONDecodeError, KeyError):
                pass  # Chain log is optional/informational

        return ChainVerificationResult(
            valid=True,
            event_count=event_count,
            chain_root=chain_root or GENESIS_HASH,
            chain_head=prev_hash,
        )

    def iter_events(self) -> Iterator[EventEnvelope]:
        """Iterate all events in sequence order."""
        envelopes = self._load_envelopes()
        yield from envelopes

    def get_event(self, seq: int) -> EventEnvelope | None:
        """Retrieve single event by sequence number."""
        envelopes = self._load_envelopes()
        for envelope in envelopes:
            if envelope.seq == seq:
                return envelope
        return None

    def get_event_payload(self, envelope: EventEnvelope) -> dict[str, Any]:
        """Load the actual event payload for an envelope."""
        event_file = self._vault_path / envelope.payload_file
        payload = json.loads(event_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Event payload must be a JSON object: {event_file}")
        return payload
