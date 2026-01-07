# Red Team Assessment Report

**Client:** [CLIENT NAME]
**Assessment Period:** [START DATE] - [END DATE]
**Report Date:** [REPORT DATE]
**Prepared By:** [ASSESSOR NAME / ORGANIZATION]

---

## Non-Claims Statement

> **IMPORTANT**: This report documents findings from heuristic-based threat detection.
> It is NOT a compliance certification, formal verification, or security guarantee.
> Hosted LLMs are non-deterministic; replay may produce different outputs.
> This is a Lane B (exploratory) evidence artifact, not Lane A (authority) governance.

---

## Executive Summary

### Scope
- **Agent Under Test:** [AGENT NAME/VERSION]
- **Environment:** [STAGING/PRODUCTION]
- **Threat Classes Assessed:**
  - [ ] Tool Misuse (OWASP ASI02, ASI03)
  - [ ] RAG/Memory Poisoning (OWASP ASI01, ASI06)
  - [ ] Privilege/Identity Misuse (OWASP ASI03)

### Key Findings

| ID | Threat Class | Severity | OWASP Tags | Status |
|----|--------------|----------|------------|--------|
| F-001 | [CLASS] | [CRITICAL/HIGH/MEDIUM/LOW] | [ASI##] | [OPEN/MITIGATED] |
| F-002 | [CLASS] | [SEVERITY] | [ASI##] | [STATUS] |

### Risk Summary
- **Critical:** [COUNT]
- **High:** [COUNT]
- **Medium:** [COUNT]
- **Low:** [COUNT]

---

## Methodology

### Attack Surface
1. LLM Input Boundary (prompts, system messages)
2. Tool/Function Calling Interface
3. RAG/Retrieval Pipeline
4. Memory/Context Management
5. Identity/Permission Model

### Test Approach
- Prompt injection attempts
- Tool invocation boundary testing
- RAG chunk poisoning simulation
- Permission escalation probes

---

## Detailed Findings

### F-001: [FINDING TITLE]

**Threat Class:** [TOOL_MISUSE | RAG_POISONING | PRIVILEGE_MISUSE]
**Severity:** [CRITICAL | HIGH | MEDIUM | LOW]
**OWASP Tags:** [ASI01, ASI02, etc.]
**Confidence:** [0.0 - 1.0]

#### Description
[Detailed description of the vulnerability]

#### Evidence
- **Bundle ID:** `run_[ID]`
- **Event Sequence:** [SEQ NUMBER]
- **Evidence Hash:** `[HASH]`

#### Reproduction
```bash
# How to reproduce
cd [BUNDLE_PATH]
python verify.py  # Verify bundle integrity first
# Then examine events/[SEQ]_[TYPE].json
```

#### Impact
[Description of potential impact if exploited]

#### Recommendation
[Specific remediation steps]

---

## Evidence Bundle Verification

### Provided Artifacts
- [ ] `replay_manifest.json` - Root manifest with hash chain
- [ ] `events/` - Captured event payloads
- [ ] `verify.py` - Standalone verification script
- [ ] `README.txt` - Bundle documentation

### How to Verify

```bash
# 1. Extract bundle
unzip [BUNDLE_NAME].zip -d ./evidence

# 2. Navigate to bundle
cd ./evidence

# 3. Run verification
python verify.py

# Expected output for intact bundle:
# Hash Chain:   [OK] INTACT
# Manifest:     [OK] VALID
# Status: EVIDENCE ARTIFACT GENERATED
```

### Verification Checklist
- [ ] Bundle unpacks without errors
- [ ] `verify.py` runs successfully
- [ ] Hash chain reports INTACT
- [ ] All referenced event files exist
- [ ] Threat flags match report findings

---

## Appendix A: OWASP Agentic Top 10 Reference

| Tag | Name | Relevance |
|-----|------|-----------|
| ASI01 | Prompt Injection | RAG poisoning, indirect injection |
| ASI02 | Insecure Tool/Plugin Design | Tool misuse, boundary violations |
| ASI03 | Excessive Agency | Privilege escalation, unauthorized actions |
| ASI04 | Overreliance on LLM Outputs | Trust boundary issues |
| ASI06 | Sensitive Information Disclosure | Data leakage via RAG |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| Evidence Bundle | Portable, hash-chained capture of agent session |
| Hash Chain | Cryptographic linkage of events for tamper detection |
| Threat Flag | Heuristic detection result with OWASP ASI mapping |
| Vault | Append-only storage with domain-separated hashing |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [DATE] | [AUTHOR] | Initial release |

---

*Generated with Agent Audit Kit v[VERSION]*
