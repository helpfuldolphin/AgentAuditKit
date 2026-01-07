"""Integration test: export bundle and verify with standalone script."""

import subprocess
import sys
from pathlib import Path

import pytest

from aak.canon.hasher import domain_hash
from aak.models.events import LLMRequestEvent, ToolCallEvent, ToolResultEvent
from aak.models.identity import ActorType, IdentityContext
from aak.vault.export import export_bundle
from aak.vault.store import VaultWriter


class TestExportAndVerify:
    """Test bundle export and standalone verification."""

    @pytest.fixture
    def populated_vault(self, tmp_path: Path) -> Path:
        """Create vault with mixed event types."""
        vault_path = tmp_path / "vault"
        writer = VaultWriter(vault_path)

        identity = IdentityContext(
            actor_type=ActorType.AGENT,
            actor_id="demo-agent",
            roles=["assistant"],
        )

        # LLM request
        writer.append_event(
            LLMRequestEvent(
                model_id="gpt-4",
                messages=[{"role": "user", "content": "Search for Q3 earnings"}],
                temperature=0.0,
                provider="openai",
                identity_context=identity,
            )
        )

        # Tool call
        tool_input = {"query": "Q3 earnings"}
        writer.append_event(
            ToolCallEvent(
                tool_name="search_kb",
                tool_input=tool_input,
                tool_input_hash=domain_hash("tool_call", tool_input),
                triggered_by_seq=0,
                identity_context=identity,
            )
        )

        # Tool result
        tool_output = {"results": ["Revenue: $4.2B", "Profit: $800M"]}
        writer.append_event(
            ToolResultEvent(
                tool_name="search_kb",
                tool_output=tool_output,
                tool_output_hash=domain_hash("tool_result", tool_output),
                latency_ms=150,
                success=True,
                call_seq=1,
                identity_context=identity,
            )
        )

        writer.finalize()
        return vault_path

    def test_export_creates_bundle(self, populated_vault: Path, tmp_path: Path):
        """Export produces expected bundle structure."""
        bundle_path = tmp_path / "bundle"
        result = export_bundle(populated_vault, bundle_path, include_verify_script=True)

        assert bundle_path.exists()
        assert (bundle_path / "replay_manifest.json").exists()
        assert (bundle_path / "events").is_dir()
        assert (bundle_path / "verify.py").exists()
        assert result.event_count == 3

    def test_verify_script_passes_on_intact_bundle(self, populated_vault: Path, tmp_path: Path):
        """Standalone verify.py passes on unmodified bundle."""
        bundle_path = tmp_path / "bundle"
        export_bundle(populated_vault, bundle_path, include_verify_script=True)

        # Run verify.py as subprocess
        result = subprocess.run(
            [sys.executable, str(bundle_path / "verify.py")],
            cwd=str(bundle_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "INTACT" in result.stdout or "OK" in result.stdout

    def test_verify_script_fails_on_tampered_bundle(self, populated_vault: Path, tmp_path: Path):
        """Standalone verify.py fails on tampered bundle."""
        bundle_path = tmp_path / "bundle"
        export_bundle(populated_vault, bundle_path, include_verify_script=True)

        # Tamper with an event
        events_dir = bundle_path / "events"
        event_files = sorted(events_dir.glob("*.json"))
        event_file = event_files[1]
        content = event_file.read_text()
        event_file.write_text(content.replace("search_kb", "hack_system"))

        # Run verify.py
        result = subprocess.run(
            [sys.executable, str(bundle_path / "verify.py")],
            cwd=str(bundle_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "FAIL" in result.stdout or "INVALID" in result.stdout

    def test_bundle_contains_readme(self, populated_vault: Path, tmp_path: Path):
        """Bundle includes README.txt."""
        bundle_path = tmp_path / "bundle"
        export_bundle(populated_vault, bundle_path)

        readme = bundle_path / "README.txt"
        assert readme.exists()
        content = readme.read_text()
        assert "Evidence Bundle" in content
        assert "DISCLAIMER" in content

    def test_manifest_contains_disclaimer(self, populated_vault: Path, tmp_path: Path):
        """Manifest includes non-claims disclaimer."""
        import json

        bundle_path = tmp_path / "bundle"
        export_bundle(populated_vault, bundle_path)

        manifest = json.loads((bundle_path / "replay_manifest.json").read_text())
        assert "disclaimer" in manifest
        assert "compliance" in manifest["disclaimer"].lower()
        assert "not" in manifest["disclaimer"].lower()
