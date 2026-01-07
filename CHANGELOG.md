# Changelog

All notable changes to Agent Audit Kit are documented here.

## [0.1.0-week2] - 2026-01-07

### Added

**Core Infrastructure**
- RFC 8785 canonical JSON serialization (`aak.canon.rfc8785`)
- Domain-separated SHA256 hashing with `aak:v0:` prefixes (`aak.canon.hasher`)
- Hash chain with genesis marker and tamper detection

**Storage**
- `VaultWriter`: Append-only event capture with hash chaining
- `VaultReader`: Verification and replay support
- `export_bundle`: Portable bundles with embedded `verify.py`

**Models**
- `EventBase` with `source: captured | synthetic` provenance field
- `IdentityContext` for non-human actor/permission tracking
- `ThreatFlag` with OWASP Agentic (ASI01-ASI10) mappings
- Event subtypes: LLMRequest, LLMResponse, ToolCall, ToolResult, RAGRetrieval

**Threat Detection**
- Three threat classes: TOOL_MISUSE, RAG_POISONING, PRIVILEGE_MISUSE
- OWASP ASI tag mapping for each class

**Demo**
- Synthetic demo harness with attack scenario
- 3 tool calls + 2 threat flags (RAG poisoning + tool misuse)

**Testing**
- 72 tests: unit (45), integration (10), acceptance (17)
- Week 1 gate: canonicalization + hashing
- Week 2 gate: vault + export + tamper detection

### Non-Claims

This release produces **evidence artifacts only**:
- NOT compliance certifications
- NOT deterministic replay of hosted LLMs
- NOT security prevention or enforcement
- Lane B exploratory; never upgrades to Lane A authority

### Verification

```bash
pip install -e ".[dev]"
python demo/harness.py --output ./demo_output
cd demo_output/bundle && python verify.py
```
