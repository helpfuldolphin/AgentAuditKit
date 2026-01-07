# Release Notes: v0.1.0-week2

**Release Date:** 2026-01-07
**Classification:** Lane B / Evidence-Only
**Status:** Week 1-2 MVP Complete

---

## Scope

This release delivers the foundational **evidence substrate** for Agent Audit Kit:

| Component | Description |
|-----------|-------------|
| Canonicalization | RFC 8785 JSON + domain-separated SHA256 |
| Vault | Append-only, hash-chained event storage |
| Export | Portable bundles with embedded verification |
| Threat Flags | OWASP ASI-mapped heuristic detection |
| Demo | Synthetic attack scenario (RAG poisoning → tool misuse) |

---

## Non-Claims (CRITICAL)

**This tool does NOT provide:**

1. **Compliance certification** — Bundles are evidence artifacts, not attestations
2. **Deterministic LLM replay** — Hosted models are non-deterministic; output may vary
3. **Security prevention** — Capture only; does not block or enforce
4. **Formal verification** — Heuristic detection, not mathematical proofs
5. **Lane A authority** — Lane B is exploratory; never upgrades to governance

---

## Reproduction Steps

```bash
# 1. Clone and install
git clone <repo>
cd agent-audit-kit
pip install -e ".[dev]"

# 2. Run tests
pytest  # 72 passed

# 3. Run demo harness
python demo/harness.py --output ./demo_output

# 4. Verify bundle
cd demo_output/bundle
python verify.py
```

**Expected verify.py output:**
```
============================================================
 AGENT AUDIT KIT - Evidence Bundle Verification
============================================================

 Bundle ID:    run_<id>
 Created:      <timestamp>
 Event Count:  10

 Hash Chain:   [OK] INTACT
 Manifest:     [OK] VALID

 THREAT FLAGS:
   [HIGH] RAG_POISONING: ASI01, ASI06
   [CRITICAL] TOOL_MISUSE: ASI02, ASI03

 Status: EVIDENCE ARTIFACT GENERATED
         (Not a compliance certification)
============================================================
```

---

## Key Invariants

1. **Single canonicalization source**: `verify.py` embeds the exact same code as `src/aak/canon/`
2. **Event hash contract**: `event_hash = domain_hash("event", payload)` — envelope fields excluded
3. **Provenance discipline**: Demo events marked `source=synthetic`

---

## Test Summary

| Suite | Count | Status |
|-------|-------|--------|
| Unit | 45 | PASS |
| Integration | 10 | PASS |
| Acceptance (W1) | 10 | PASS |
| Acceptance (W2) | 7 | PASS |
| **Total** | **72** | **PASS** |

---

## Files

```
agent-audit-kit/
├── src/aak/
│   ├── canon/          # RFC 8785 + domain hashing
│   ├── models/         # Event, Identity, Threat, Manifest
│   └── vault/          # Writer, Reader, Export
├── demo/
│   ├── harness.py      # Synthetic attack demo
│   └── mock_tools.py   # Fake KB with poisoned chunk
├── tests/
│   ├── unit/           # 45 tests
│   ├── integration/    # 10 tests
│   └── acceptance/     # 17 tests
├── CHANGELOG.md
├── RUNBOOK.md          # 15-minute demo walkthrough
└── README.md
```

---

## Next (Week 3)

- Real capture integration (OpenAI wrapper)
- `examples/real_capture_demo.py`
- Client-facing templates (red team, IR playbook, evidence pack)
