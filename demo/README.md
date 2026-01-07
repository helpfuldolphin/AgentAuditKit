# Agent Audit Kit - Demo Guide

**Duration:** 10–15 minutes  
**Format:** Terminal screen capture  
**Audience:** Security teams, insurers, auditors, legal

---

## Before You Start

1. Open terminal in `agent-audit-kit/` root
2. Ensure Python 3.11+ installed
3. Run `pip install -e .` or `uv sync`
4. Maximize terminal window (readable font size)

---

## Running the Demo

**Windows:**
```powershell
./demo/run_demo.ps1
```

**Linux/Mac:**
```bash
./demo/run_demo.sh
```

---

## Speaker Notes

### Opening (1 min)

> "AI agents act autonomously. When something goes wrong, traditional logs show *what* happened but not *why*. Agent Audit Kit captures the full decision context — every LLM call, every tool invocation, every retrieval — in a tamper-evident chain."

**Key point:** This is forensic evidence, not compliance certification.

---

### Step 1: Clear Previous Output (30 sec)

> "We start fresh. No cached results, no pre-baked demos."

**Show:** Clean slate, deterministic starting point.

---

### Step 2: Agent Capture (3 min)

> "This is a financial assistant agent making real decisions. It's calling three tools: weather, stock price, and news search. Every request, response, and tool call is being captured with cryptographic hashes."

**Watch for:**
- `[DEMO] Event N: LLM request` — request captured
- `[DEMO] Event N: LLM response` — response captured
- `[DEMO] Tool call: get_weather(...)` — tool invocation recorded
- `[DEMO] Session finalized. Chain head: ...` — hash chain sealed

**Key point:** The `source: CAPTURED` label distinguishes real traffic from synthetic test data.

---

### Step 3: Bundle Verification (2 min)

> "The bundle includes a standalone verification script. No AAK installation required. An auditor, insurer, or opposing counsel can verify this independently."

**Watch for:**
- `Hash Chain: [OK] INTACT` — no tampering detected
- `Manifest: [OK] VALID` — all events accounted for
- `Status: EVIDENCE ARTIFACT GENERATED` — not a compliance cert

**Key point:** If anyone modifies even one byte, the chain breaks.

---

### Step 4: Threat Detection (2 min)

> "The system flagged this session for potential excessive agency — three tool calls in rapid succession. This is a heuristic, not a verdict. It surfaces patterns for human review."

**Watch for:**
- `[LOW] PRIVILEGE_MISUSE` — threat class
- `OWASP Tags: ASI03, ASI04` — industry-standard mapping
- Description of what triggered the flag

**Key point:** Threat flags are starting points for investigation, not automated decisions.

---

### Closing (2 min)

> "This bundle can be attached to an incident report, supplied to an insurer, or presented in legal discovery. It's portable, verifiable, and makes no truth claims."

**Artifacts to highlight:**
- `replay_manifest.json` — root of trust
- `events/*.json` — individual event payloads
- `verify.py` — standalone verifier (copy to USB, email to auditor)

---

## Common Questions

**Q: Can I replay the exact LLM outputs?**  
A: No. Hosted LLMs are non-deterministic. We verify capture integrity, not output reproduction.

**Q: Is this a compliance certification?**  
A: No. This is evidence for human review, not automated trust assignment.

**Q: What if I need governance-grade verification?**  
A: That's Lane A (e.g., MathLedger). Agent Audit Kit is Lane B — forensic, exploratory.

**Q: Can this replace my SIEM?**  
A: No. SIEMs aggregate logs. AAK captures decision context with cryptographic integrity. They're complementary.

---

## Post-Demo

Leave the audience with:
1. The bundle directory (zip and share)
2. This README for reference
3. The explicit statement: *"Agent Audit Kit produces evidence artifacts, not truth claims."*

---

*Agent Audit Kit v0.1.1-week3*
