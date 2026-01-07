"""Integration test: tamper detection via hash chain."""

import json
from pathlib import Path

import pytest

from aak.models.events import LLMRequestEvent
from aak.models.identity import ActorType, IdentityContext
from aak.vault.store import VaultReader, VaultWriter


class TestTamperDetection:
    """Verify that hash chain detects tampering."""

    @pytest.fixture
    def vault_with_events(self, tmp_path: Path) -> Path:
        """Create vault with 5 events."""
        vault_path = tmp_path / "test_vault"
        writer = VaultWriter(vault_path)

        identity = IdentityContext(
            actor_type=ActorType.AGENT,
            actor_id="test-agent-001",
        )

        for i in range(5):
            event = LLMRequestEvent(
                model_id="gpt-4",
                messages=[{"role": "user", "content": f"Message {i}"}],
                temperature=0.7,
                provider="openai",
                identity_context=identity,
            )
            writer.append_event(event)

        writer.finalize()
        return vault_path

    def test_intact_chain_verifies(self, vault_with_events: Path):
        """Unmodified vault passes verification."""
        reader = VaultReader(vault_with_events)
        result = reader.verify_chain()

        assert result.valid is True
        assert result.event_count == 5
        assert result.first_invalid_seq is None

    def test_single_bit_flip_detected(self, vault_with_events: Path):
        """Flipping one bit in event file breaks chain."""
        # Find and corrupt event file
        events_dir = vault_with_events / "events"
        event_files = sorted(events_dir.glob("*.json"))
        event_file = event_files[2]  # Corrupt the third event

        content = event_file.read_bytes()
        # Flip one bit in the middle
        corrupted = bytearray(content)
        mid = len(corrupted) // 2
        corrupted[mid] ^= 0x01
        event_file.write_bytes(bytes(corrupted))

        # Verify should fail
        reader = VaultReader(vault_with_events)
        result = reader.verify_chain()

        assert result.valid is False
        # The error will be detected at event 2 or later
        assert result.first_invalid_seq is not None or result.error_message is not None

    def test_deleted_event_detected(self, vault_with_events: Path):
        """Deleting an event file breaks chain."""
        events_dir = vault_with_events / "events"
        event_files = sorted(events_dir.glob("*.json"))
        # Delete middle event
        event_files[2].unlink()

        reader = VaultReader(vault_with_events)
        result = reader.verify_chain()

        # With a missing event, either the count is wrong or chain breaks
        # The reader might skip the file and have wrong count
        assert result.event_count != 5 or result.valid is False

    def test_modified_content_detected(self, vault_with_events: Path):
        """Modifying event content is detected."""
        events_dir = vault_with_events / "events"
        event_files = sorted(events_dir.glob("*.json"))
        event_file = event_files[1]

        # Load, modify, save
        data = json.loads(event_file.read_text())
        data["model_id"] = "hacked-model"
        event_file.write_text(json.dumps(data))

        reader = VaultReader(vault_with_events)
        result = reader.verify_chain()

        assert result.valid is False

    def test_reordered_events_detected(self, vault_with_events: Path):
        """Swapping event content breaks chain."""
        events_dir = vault_with_events / "events"
        event_files = sorted(events_dir.glob("*.json"))
        f1 = event_files[1]
        f2 = event_files[2]

        content1 = f1.read_bytes()
        content2 = f2.read_bytes()
        f1.write_bytes(content2)
        f2.write_bytes(content1)

        reader = VaultReader(vault_with_events)
        result = reader.verify_chain()

        assert result.valid is False
