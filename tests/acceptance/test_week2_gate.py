"""Week 2 acceptance gate tests."""

import json
from pathlib import Path

import pytest

from aak.canon.hasher import domain_hash
from aak.models.events import (
    EventSource,
    LLMRequestEvent,
    SessionStartEvent,
    ToolCallEvent,
)
from aak.models.identity import ActorType, IdentityContext
from aak.vault.export import export_bundle
from aak.vault.store import VaultReader, VaultSealedError, VaultWriter


class TestWeek2AcceptanceCriteria:
    """
    Week 2 Gate:
    - Vault append creates hash-chained events
    - Vault finalize seals and returns chain head
    - verify_chain passes on intact vault
    - verify_chain fails on tampered vault (single byte flip)
    - export_bundle creates portable structure with verify.py
    """

    @pytest.fixture
    def identity(self) -> IdentityContext:
        return IdentityContext(
            actor_type=ActorType.AGENT,
            actor_id="test-agent",
            roles=["assistant"],
            permissions=["read", "search"],
        )

    def test_vault_append_returns_envelope(self, tmp_path: Path, identity):
        """AC-W2-01: append_event returns envelope with hash chain."""
        writer = VaultWriter(tmp_path / "vault")
        event = LLMRequestEvent(
            model_id="gpt-4",
            messages=[],
            provider="openai",
            identity_context=identity,
        )
        envelope = writer.append_event(event)

        assert envelope.seq == 0
        assert len(envelope.hash) == 64
        assert len(envelope.prev_hash) == 64

    def test_vault_finalize_seals(self, tmp_path: Path, identity):
        """AC-W2-02: finalize() seals vault and returns chain head."""
        writer = VaultWriter(tmp_path / "vault")
        for i in range(3):
            writer.append_event(
                LLMRequestEvent(
                    model_id="gpt-4",
                    messages=[{"role": "user", "content": f"msg {i}"}],
                    provider="openai",
                    identity_context=identity,
                )
            )

        chain_head = writer.finalize()
        assert len(chain_head) == 64

        # Further writes should fail
        with pytest.raises(VaultSealedError):
            writer.append_event(LLMRequestEvent(model_id="gpt-4", messages=[], provider="openai"))

    def test_verify_chain_passes_intact(self, tmp_path: Path, identity):
        """AC-W2-03: verify_chain passes on unmodified vault."""
        vault_path = tmp_path / "vault"
        writer = VaultWriter(vault_path)
        for i in range(5):
            writer.append_event(
                LLMRequestEvent(
                    model_id="gpt-4",
                    messages=[{"role": "user", "content": f"msg {i}"}],
                    provider="openai",
                    identity_context=identity,
                )
            )
        writer.finalize()

        reader = VaultReader(vault_path)
        result = reader.verify_chain()

        assert result.valid is True
        assert result.event_count == 5

    def test_verify_chain_fails_on_tamper(self, tmp_path: Path, identity):
        """AC-W2-04: Single byte flip -> verify_chain fails."""
        vault_path = tmp_path / "vault"
        writer = VaultWriter(vault_path)
        for i in range(3):
            writer.append_event(
                LLMRequestEvent(
                    model_id="gpt-4",
                    messages=[{"role": "user", "content": f"msg {i}"}],
                    provider="openai",
                    identity_context=identity,
                )
            )
        writer.finalize()

        # Corrupt event 1
        events_dir = vault_path / "events"
        event_files = sorted(events_dir.glob("*.json"))
        event_file = event_files[1]
        data = bytearray(event_file.read_bytes())
        data[50] ^= 0x01
        event_file.write_bytes(bytes(data))

        reader = VaultReader(vault_path)
        result = reader.verify_chain()

        assert result.valid is False

    def test_export_bundle_structure(self, tmp_path: Path, identity):
        """AC-W2-05: export_bundle creates correct structure."""
        vault_path = tmp_path / "vault"
        bundle_path = tmp_path / "bundle"

        writer = VaultWriter(vault_path)
        writer.append_event(
            SessionStartEvent(
                run_id=writer.run_id,
                sdk_version="0.1.0",
                vault_path=str(vault_path),
                identity_context=identity,
            )
        )
        writer.append_event(
            ToolCallEvent(
                tool_name="search",
                tool_input={"q": "test"},
                tool_input_hash=domain_hash("tool_call", {"q": "test"}),
                identity_context=identity,
            )
        )
        writer.finalize()

        result = export_bundle(vault_path, bundle_path)

        assert (bundle_path / "replay_manifest.json").exists()
        assert (bundle_path / "events").is_dir()
        assert (bundle_path / "verify.py").exists()
        assert result.event_count == 2

    def test_event_source_provenance(self, tmp_path: Path, identity):
        """AC-W2-06: Events have source field for provenance."""
        writer = VaultWriter(tmp_path / "vault")

        # Captured event (default)
        captured = LLMRequestEvent(
            model_id="gpt-4",
            messages=[],
            provider="openai",
        )
        assert captured.source == EventSource.CAPTURED

        # Synthetic event (explicit)
        synthetic = LLMRequestEvent(
            model_id="gpt-4",
            messages=[],
            provider="openai",
            source=EventSource.SYNTHETIC,
        )
        assert synthetic.source == EventSource.SYNTHETIC

        # Both can be appended
        writer.append_event(captured)
        writer.append_event(synthetic)
        writer.finalize()

    def test_manifest_has_events_array(self, tmp_path: Path, identity):
        """AC-W2-07: Manifest contains events array with envelopes."""
        vault_path = tmp_path / "vault"
        bundle_path = tmp_path / "bundle"

        writer = VaultWriter(vault_path)
        writer.append_event(
            LLMRequestEvent(
                model_id="gpt-4",
                messages=[],
                provider="openai",
            )
        )
        writer.finalize()

        export_bundle(vault_path, bundle_path)

        manifest = json.loads((bundle_path / "replay_manifest.json").read_text())
        assert "events" in manifest
        assert len(manifest["events"]) == 1
        assert "hash" in manifest["events"][0]
        assert "prev_hash" in manifest["events"][0]
        assert "seq" in manifest["events"][0]
