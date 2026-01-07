"""Unit tests for vault storage."""

from pathlib import Path

import pytest

from aak.canon.hasher import GENESIS_HASH
from aak.models.events import LLMRequestEvent
from aak.models.identity import ActorType, IdentityContext
from aak.vault.store import VaultReader, VaultSealedError, VaultWriter


class TestVaultWriter:
    """Test suite for VaultWriter."""

    def test_create_vault(self, tmp_path: Path):
        """VaultWriter creates vault directory structure."""
        vault_path = tmp_path / "vault"
        writer = VaultWriter(vault_path)

        assert vault_path.exists()
        assert (vault_path / "events").exists()
        assert writer.run_id.startswith("run_")

    def test_append_event_returns_envelope(self, tmp_path: Path):
        """append_event returns envelope with hash chain."""
        writer = VaultWriter(tmp_path / "vault")
        event = LLMRequestEvent(
            model_id="gpt-4",
            messages=[],
            provider="openai",
        )
        envelope = writer.append_event(event)

        assert envelope.seq == 0
        assert len(envelope.hash) == 64
        assert envelope.prev_hash == GENESIS_HASH

    def test_append_multiple_events(self, tmp_path: Path):
        """Multiple events chain correctly."""
        writer = VaultWriter(tmp_path / "vault")

        for i in range(3):
            event = LLMRequestEvent(
                model_id="gpt-4",
                messages=[{"role": "user", "content": f"msg {i}"}],
                provider="openai",
            )
            envelope = writer.append_event(event)
            assert envelope.seq == i

    def test_chain_head_updates(self, tmp_path: Path):
        """chain_head updates after each append."""
        writer = VaultWriter(tmp_path / "vault")
        initial_head = writer.chain_head

        event = LLMRequestEvent(
            model_id="gpt-4",
            messages=[],
            provider="openai",
        )
        writer.append_event(event)

        assert writer.chain_head != initial_head

    def test_finalize_seals_vault(self, tmp_path: Path):
        """finalize() prevents further writes."""
        writer = VaultWriter(tmp_path / "vault")
        event = LLMRequestEvent(
            model_id="gpt-4",
            messages=[],
            provider="openai",
        )
        writer.append_event(event)
        writer.finalize()

        with pytest.raises(VaultSealedError):
            writer.append_event(event)

    def test_finalize_returns_chain_head(self, tmp_path: Path):
        """finalize() returns final chain head."""
        writer = VaultWriter(tmp_path / "vault")
        event = LLMRequestEvent(
            model_id="gpt-4",
            messages=[],
            provider="openai",
        )
        writer.append_event(event)
        chain_head = writer.finalize()

        assert len(chain_head) == 64
        assert chain_head == writer.chain_head

    def test_event_files_created(self, tmp_path: Path):
        """Event files are created in events/ directory."""
        vault_path = tmp_path / "vault"
        writer = VaultWriter(vault_path)
        event = LLMRequestEvent(
            model_id="gpt-4",
            messages=[],
            provider="openai",
        )
        envelope = writer.append_event(event)
        writer.finalize()

        event_file = vault_path / envelope.payload_file
        assert event_file.exists()


class TestVaultReader:
    """Test suite for VaultReader."""

    @pytest.fixture
    def populated_vault(self, tmp_path: Path) -> Path:
        """Create a vault with events."""
        vault_path = tmp_path / "vault"
        writer = VaultWriter(vault_path)

        identity = IdentityContext(
            actor_type=ActorType.AGENT,
            actor_id="test-agent",
        )

        for i in range(5):
            event = LLMRequestEvent(
                model_id="gpt-4",
                messages=[{"role": "user", "content": f"msg {i}"}],
                provider="openai",
                identity_context=identity,
            )
            writer.append_event(event)

        writer.finalize()
        return vault_path

    def test_verify_chain_passes(self, populated_vault: Path):
        """verify_chain passes on intact vault."""
        reader = VaultReader(populated_vault)
        result = reader.verify_chain()

        assert result.valid is True
        assert result.event_count == 5
        assert result.first_invalid_seq is None

    def test_iter_events(self, populated_vault: Path):
        """iter_events yields all events in order."""
        reader = VaultReader(populated_vault)
        envelopes = list(reader.iter_events())

        assert len(envelopes) == 5
        for i, env in enumerate(envelopes):
            assert env.seq == i

    def test_get_event(self, populated_vault: Path):
        """get_event retrieves by sequence number."""
        reader = VaultReader(populated_vault)
        envelope = reader.get_event(2)

        assert envelope is not None
        assert envelope.seq == 2

    def test_get_event_not_found(self, populated_vault: Path):
        """get_event returns None for missing seq."""
        reader = VaultReader(populated_vault)
        envelope = reader.get_event(999)

        assert envelope is None

    def test_get_event_payload(self, populated_vault: Path):
        """get_event_payload loads event data."""
        reader = VaultReader(populated_vault)
        envelope = reader.get_event(0)
        assert envelope is not None

        payload = reader.get_event_payload(envelope)
        assert payload["event_type"] == "llm_request"
        assert payload["model_id"] == "gpt-4"
