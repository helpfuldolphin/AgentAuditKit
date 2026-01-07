# Agent Audit Kit

Forensic evidence capture and replay for AI agents — designed for incident response, red teaming, and audit review, not governance or compliance certification.

[![CI](https://github.com/your-org/agent-audit-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/agent-audit-kit/actions/workflows/ci.yml)

## Overview

Agent Audit Kit (AAK) provides tamper-evident capture and replay of AI agent interactions for forensic analysis and incident response.

**Lane B / Exploratory (Forensic)**

Agent Audit Kit is intentionally non-authoritative.
It captures *what happened*, not *what is correct*.

It is designed to support:
- incident response
- red team exercises
- insurance and legal review
- auditor inspection of agent behavior

It does not determine truth, correctness, or admissibility.

## Intended Users

- Security teams (SOC / IR)
- Red team operators
- AI risk and trust teams
- Legal and compliance reviewers
- Insurers and third-party auditors

This tool is not intended to certify correctness or safety.

## Non-Claims Discipline

**IMPORTANT**: This tool does NOT provide:

- Compliance certification
- Deterministic replay of hosted LLMs (they are non-deterministic)
- Formal verification or proofs
- Governance-grade authority (that's Lane A / MathLedger)

What it DOES provide:

- Tamper-evident hash chains for event capture
- Domain-separated SHA256 hashing (RFC 8785 canonical JSON)
- OWASP Agentic (ASI) threat detection mappings
- Portable evidence bundles with standalone verification
- Provenance labeling (`captured` vs `synthetic`)

## Lane Boundary Rule (Hard)

Agent Audit Kit artifacts are **evidence only**.

They may be:
- reviewed by humans
- attached to audit reports
- supplied to insurers, regulators, or courts

They may NOT be:
- treated as verified claims
- used to assign trust class
- used to upgrade authority
- substituted for governance-grade verification

Authority decisions belong to Lane A systems (e.g. MathLedger),
not to this tool.

## Quickstart

```bash
# Install dependencies
pip install -e ".[dev]"
# or with uv:
uv sync --dev

# Run tests
pytest

# Run demo harness
python demo/harness.py --output ./demo_output

# Verify the bundle
cd demo_output/bundle && python verify.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENT RUNTIME                                │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │ LLM Client   │   │ Tool Router  │   │ RAG/Memory   │            │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘            │
│         └──────────────────┼──────────────────┘                     │
│                            ▼                                        │
│              ┌─────────────────────────────┐                        │
│              │   CONTEXT INTERCEPTOR SDK   │                        │
│              └─────────────┬───────────────┘                        │
└────────────────────────────┼────────────────────────────────────────┘
                             ▼
              ┌─────────────────────────────┐
              │      IMMUTABLE VAULT        │
              │  (append-only, hash-chained)│
              └─────────────┬───────────────┘
                            ▼
              ┌─────────────────────────────┐
              │     REPLAY / ANALYSIS       │
              │  (forensic or counterfactual)│
              └─────────────────────────────┘
```

**Note**: Replay verifies capture integrity and event ordering.
It does not imply deterministic re-execution of hosted LLMs.

## Key Components

### Canonicalization (`aak.canon`)

- RFC 8785 compliant canonical JSON
- Domain-separated SHA256 hashing
- Identical code embedded in verify.py for consistency

### Models (`aak.models`)

- `EventBase` with `source: captured | synthetic`
- `IdentityContext` for non-human actor tracking
- `ThreatFlag` with OWASP ASI mappings (ASI01-ASI10)

### Vault (`aak.vault`)

- `VaultWriter`: Append-only event storage with hash chaining
- `VaultReader`: Verification and replay support
- `export_bundle`: Portable bundles with embedded verify.py

## Event Hashing Contract

The `event_hash` is computed as:

```python
event_hash = domain_hash("event", canonical_event_payload)
```

Where:
- `canonical_event_payload` is the RFC 8785 canonical JSON of the event
- Envelope fields (`seq`, `hash`, `prev_hash`, `payload_file`) are NOT included
- Domain prefix is `aak:v0:event:`

## Threat Detection

Three threat classes mapped to OWASP Agentic Top 10:

| Threat Class | OWASP ASI Tags |
|--------------|----------------|
| TOOL_MISUSE | ASI02, ASI03 |
| RAG_POISONING | ASI01, ASI06 |
| PRIVILEGE_MISUSE | ASI03 |

## Development

```bash
# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run specific test suites
pytest tests/unit -v
pytest tests/integration -v
pytest tests/acceptance -v
```

## License

Apache-2.0
