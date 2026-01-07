# Selling the Wedge

## The Problem: Agents Act, Logs Don't Explain

AI agents make decisions, invoke tools, and take actions autonomously.
When something goes wrong, traditional logs show *what happened* but not *why*.

- LLM responses are opaque
- Tool invocations lack context
- Memory/RAG retrievals aren't captured
- There's no chain of custody for forensic review

Incident responders and auditors face a black box.

## The Wedge: Deterministic Capture + Replayable Evidence

Agent Audit Kit captures the full decision context:

1. **Every LLM request/response** with model ID, tokens, and timing
2. **Every tool call** with inputs, outputs, and identity context
3. **Every RAG retrieval** with chunk hashes and source attribution
4. **Hash-chained events** for tamper-evident storage

The result: portable evidence bundles that can be verified independently,
shared with insurers, or attached to incident reports.

## What This Is NOT

| Not This | Why Not |
|----------|---------|
| **SIEM** | SIEMs aggregate logs. AAK captures decision context with cryptographic integrity. |
| **Guardrails** | Guardrails prevent actions. AAK records what happened for post-hoc analysis. |
| **Compliance tool** | Compliance requires authority. AAK produces evidence, not certification. |
| **Deterministic replay** | Hosted LLMs are non-deterministic. AAK verifies capture integrity, not output reproduction. |

## How This Complements Governance Systems

Agent Audit Kit is **Lane B** (exploratory/forensic).
Governance systems like MathLedger are **Lane A** (authoritative/deterministic).

```
┌─────────────────────────────────────────────────────────────┐
│                     AGENT RUNTIME                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   LANE A            │       │   LANE B            │
│   Governance        │       │   Forensics         │
│   (MathLedger)      │       │   (Agent Audit Kit) │
│                     │       │                     │
│   - Trust class     │       │   - Evidence only   │
│   - Verified claims │       │   - Heuristic flags │
│   - Authority       │       │   - Human review    │
└─────────────────────┘       └─────────────────────┘
```

**The boundary is hard:**
- Lane A artifacts grant authority
- Lane B artifacts support investigation

Agent Audit Kit never upgrades to Lane A.
It provides the evidence that humans and Lane A systems can evaluate.

## The Value Proposition

For **security teams**: Forensic evidence for incident response
For **red teams**: Replayable attack scenarios with full context
For **insurers**: Underwriting evidence with cryptographic integrity
For **auditors**: Tamper-evident trails for compliance review
For **legal**: Discovery-ready evidence bundles

One capture system. Multiple downstream consumers. No authority claims.
