# Agent Audit Kit — 15-Minute Demo Runbook

This runbook walks through the complete demo scenario for Agent Audit Kit.

## Prerequisites

- Python 3.11+
- Repository cloned and dependencies installed

```bash
cd agent-audit-kit
pip install -e ".[dev]"
# or: uv sync --dev
```

## Demo Scenario Overview

**Scenario**: A document summarization agent is tricked by a poisoned RAG chunk into attempting to access sensitive employee SSNs.

**Key Events**:
1. Agent receives request to summarize Q3 earnings
2. Agent calls `search_kb` tool
3. Retrieved chunks include poisoned content with injection
4. Agent follows injection and attempts to call `get_employee_ssn_list`
5. Tool access is blocked (insufficient permissions)
6. Agent falls back to safe `calculate_metrics` tool

**Threat Flags Generated**:
- RAG_POISONING (ASI01, ASI06): Injection pattern in retrieved chunk
- TOOL_MISUSE (ASI02, ASI03): Unauthorized tool invocation attempt

---

## Step 1: Run the Demo Harness (2 min)

```bash
python demo/harness.py --output ./demo_output
```

**Expected Output**:
```
[DEMO] Starting capture session: run_abc12345
[DEMO] All events marked as SYNTHETIC for provenance discipline

[DEMO] Event 0: LLM request
[DEMO] Event 1: LLM response (tool_calls)
[DEMO] Event 2: Tool call search_kb
[DEMO] Event 3: Tool result (contains poisoned chunk)
[DEMO] THREAT FLAG: RAG_POISONING (ASI01, ASI06)
[DEMO] Event 4: LLM response (malicious tool call)
[DEMO] Event 5: Tool call get_employee_ssn_list (MISUSE)
[DEMO] THREAT FLAG: TOOL_MISUSE (ASI02, ASI03)
[DEMO] Event 6: Tool result (blocked)
[DEMO] Event 7: Tool call calculate_metrics (safe)
[DEMO] Event 8: Tool result (metrics)

[DEMO] Session finalized. Chain head: a1b2c3d4...
[DEMO] Total events: 10
[DEMO] Threat flags: 2

[DEMO] Exporting bundle to demo_output/bundle
...
```

---

## Step 2: Inspect the Bundle (2 min)

```bash
ls -la demo_output/bundle/
```

**Expected Structure**:
```
demo_output/bundle/
├── replay_manifest.json    # Root manifest with hash chain
├── events/                 # Individual event files
│   ├── 000_session_start.json
│   ├── 001_llm_request.json
│   ├── 002_llm_response.json
│   ├── 003_tool_call.json
│   ├── 004_tool_result.json
│   ├── 005_llm_response.json
│   ├── 006_tool_call.json
│   ├── 007_tool_result.json
│   ├── 008_tool_call.json
│   └── 009_tool_result.json
├── verify.py               # Standalone verification script
└── README.txt              # Bundle documentation
```

**Check the manifest**:
```bash
cat demo_output/bundle/replay_manifest.json | python -m json.tool | head -30
```

---

## Step 3: Verify Bundle Integrity (2 min)

```bash
cd demo_output/bundle && python verify.py
```

**Expected Output**:
```
============================================================
 AGENT AUDIT KIT - Evidence Bundle Verification
============================================================

 Bundle ID:    run_abc12345
 Created:      2026-01-07T10:30:00Z
 Event Count:  10

 Hash Chain:   [OK] INTACT
 Manifest:     [OK] VALID

 THREAT FLAGS:
   [HIGH] RAG_POISONING: ASI01, ASI06
           Injection pattern detected in retrieved chunk...
   [CRITICAL] TOOL_MISUSE: ASI02, ASI03
           Tool 'get_employee_ssn_list' invoked without...

 Status: EVIDENCE ARTIFACT GENERATED
         (Not a compliance certification)

============================================================
```

---

## Step 4: Demonstrate Tamper Detection (3 min)

**Corrupt an event file**:
```bash
cd demo_output/bundle

# Backup original
cp events/003_tool_call.json events/003_tool_call.json.bak

# Tamper with the file
sed -i 's/search_kb/hack_tool/g' events/003_tool_call.json
# On Windows: powershell -Command "(Get-Content events/003_tool_call.json) -replace 'search_kb','hack_tool' | Set-Content events/003_tool_call.json"
```

**Re-run verification**:
```bash
python verify.py
```

**Expected Output**:
```
============================================================
 AGENT AUDIT KIT - Evidence Bundle Verification
============================================================

 Hash Chain:   [FAIL] INVALID
 Error:        Event 3: hash mismatch (tampering detected)

 Status: VERIFICATION FAILED

============================================================
```

**Restore and verify**:
```bash
cp events/003_tool_call.json.bak events/003_tool_call.json
python verify.py  # Should pass again
```

---

## Step 5: Examine Threat Evidence (3 min)

**View the RAG poisoning evidence**:
```bash
cat events/004_tool_result.json | python -m json.tool
```

Look for the poisoned chunk with `SYSTEM:` injection pattern.

**View the tool misuse evidence**:
```bash
cat events/006_tool_call.json | python -m json.tool
```

Note:
- `tool_name`: `get_employee_ssn_list`
- `source`: `synthetic` (provenance marker)
- Identity context shows agent only has `["read:documents", "compute"]` permissions

---

## Step 6: Review Event Provenance (2 min)

All demo events are marked with `"source": "synthetic"` to clearly distinguish them from real captured events.

```bash
grep -l '"source": "synthetic"' events/*.json | wc -l
```

This ensures demo artifacts can never be confused with actual incident evidence.

---

## Summary

| Step | Time | Key Action |
|------|------|------------|
| 1 | 2 min | Run `demo/harness.py` |
| 2 | 2 min | Inspect bundle structure |
| 3 | 2 min | Run `verify.py` (passes) |
| 4 | 3 min | Tamper and re-verify (fails) |
| 5 | 3 min | Examine threat evidence |
| 6 | 2 min | Check provenance markers |
| **Total** | **14 min** | |

---

## Key Takeaways

1. **Hash Chain Integrity**: Any modification to event files is detected
2. **Domain-Separated Hashing**: RFC 8785 canonical JSON ensures deterministic hashes
3. **OWASP ASI Mapping**: Threat flags link to industry-standard categories
4. **Provenance Discipline**: Synthetic events are clearly labeled
5. **Portable Bundles**: verify.py is self-contained and works offline

---

## Non-Claims Reminder

This demo produces **evidence artifacts**, NOT:
- Compliance certifications
- Deterministic replay guarantees for hosted LLMs
- Formal verification proofs

For governance-grade verification, see Lane A (MathLedger).
