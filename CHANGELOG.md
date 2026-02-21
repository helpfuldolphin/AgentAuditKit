# Changelog

All notable changes to Agent Audit Kit are documented here.

## [0.2.0-psych-context] - 2026-02-21

### Added

- Optional `psych_context` event extension (`hash_ref` default, `inline_minimal` optional).
- New psych models: `PsychContext`, `PsychIndicator`, `PsychCaptureMode`, and context hash helper.
- Optional psych metadata fields on replay manifest session metadata.
- Optional interceptor provider protocol for live psych context capture (`PsychContextProvider`).
- New contract: `docs/contracts/CPF_CONTEXT_CONTRACT_V0_2.md`.
- New acceptance gate: `tests/acceptance/test_week8_psych_context_gate.py`.
- New golden-run generator: `examples/generate_psych_golden_run.py`.
- New golden run artifact pack: `golden_runs/aak-v0.2.0-psych-ceo-cac/`.

### Changed

- Replay verification now fail-closes on declared psych artifact mismatch (missing/extra/modified).
- Embedded bundle `verify.py` now validates optional psych artifact references and hashes.
- Bundle export now copies optional `psych/` artifacts and records psych metadata when present.
- Deterministic report adds `Psychological Context (Captured/Referenced)` section.
- Report CLI output now includes psych context count.

### Non-Claims

- Psych context linkage remains Lane B evidence-only.
- No governance authority assignment, compliance certification, or Lane A trust-class semantics.

## [0.1.1-report] - 2026-02-18

### Added

- `aak report generate --bundle ... --out ...` deterministic report command.
- `audit_report.md` derived artifact generation (fixed template, explicit `UNKNOWN` fields).
- report contract: `docs/contracts/AUDIT_REPORT_CONTRACT_V0_1.md`.
- acceptance gates for:
  - byte-identical report determinism
  - tamper -> fail-closed behavior
  - banned overclaiming vocabulary in report text

### Changed

- Golden run evidence pack now includes report generation command, `audit_report.md`, and `report_hash`.
- `.gitignore` now excludes `examples/openclaw/output/` generated artifacts.

### Non-Claims

- Report layer remains evidence-only and non-authoritative.
- No intent/causality inference.
- No correctness/safety/compliance guarantees.

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
