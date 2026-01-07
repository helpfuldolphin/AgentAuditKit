# Evidence Pack Handoff Document

**Engagement:** [ENGAGEMENT NAME]
**Client:** [CLIENT NAME]
**Handoff Date:** [DATE]
**Prepared By:** [ASSESSOR NAME]
**Recipient:** [CLIENT CONTACT]

---

## Non-Claims Statement

> **CRITICAL**: Read this section carefully before accepting the evidence pack.

This evidence pack contains **forensic evidence artifacts**, NOT:
- Compliance certifications
- Security guarantees
- Formal verification proofs
- Deterministic replay guarantees for hosted LLMs

**What this evidence pack IS:**
- Hash-chained capture of agent sessions
- Heuristic threat detection results
- Tamper-evident storage suitable for audit review
- Lane B (exploratory) output, not Lane A (authority) governance

**By accepting this evidence pack, you acknowledge:**
1. The findings are heuristic-based and should be reviewed by qualified personnel
2. Hosted LLMs are non-deterministic; replay may produce different outputs
3. The evidence supports investigation, not automated decision-making
4. All claims in associated reports are subject to the limitations above

---

## Evidence Pack Contents

### Bundle Inventory

| File/Directory | Description | Hash Verified |
|----------------|-------------|---------------|
| `replay_manifest.json` | Root manifest with hash chain | [ ] |
| `events/` | Individual event payloads | [ ] |
| `verify.py` | Standalone verification script | [ ] |
| `README.txt` | Bundle documentation | [ ] |

### Associated Documents

| Document | Filename | Included |
|----------|----------|----------|
| Red Team Report | `RED_TEAM_REPORT_[DATE].pdf` | [ ] |
| IR Playbook | `IR_PLAYBOOK_[VERSION].pdf` | [ ] |
| This Handoff Doc | `EVIDENCE_PACK_HANDOFF.md` | [x] |

---

## How to Verify the Bundle

### Prerequisites
- Python 3.11 or higher
- No additional dependencies required

### Verification Steps

```bash
# Step 1: Extract the evidence pack
unzip evidence_pack_[ENGAGEMENT_ID].zip -d ./evidence

# Step 2: Navigate to the bundle directory
cd ./evidence/bundle

# Step 3: Run the verification script
python verify.py
```

### Expected Output (Intact Bundle)

```
============================================================
 AGENT AUDIT KIT - Evidence Bundle Verification
============================================================

 Bundle ID:    run_[ID]
 Created:      [TIMESTAMP]
 Event Count:  [N]

 Hash Chain:   [OK] INTACT
 Manifest:     [OK] VALID

 THREAT FLAGS:
   [SEVERITY] [THREAT_CLASS]: [ASI_TAGS]
   ...

 Status: EVIDENCE ARTIFACT GENERATED
         (Not a compliance certification)

============================================================
```

### Expected Output (Tampered Bundle)

```
============================================================
 AGENT AUDIT KIT - Evidence Bundle Verification
============================================================

 Hash Chain:   [FAIL] INVALID
 Error:        Event [N]: hash mismatch (tampering detected)

 Status: VERIFICATION FAILED

============================================================
```

### Verification Checklist

- [ ] Bundle extracts without errors
- [ ] `python verify.py` exits with code 0
- [ ] "Hash Chain: [OK] INTACT" displayed
- [ ] "Manifest: [OK] VALID" displayed
- [ ] Threat flag count matches Red Team Report
- [ ] Bundle ID matches engagement records

---

## Evidence Summary

### Session Details

| Attribute | Value |
|-----------|-------|
| Bundle ID | `run_[ID]` |
| Created | [TIMESTAMP] |
| Event Count | [N] |
| Chain Root | `[HASH_PREFIX]...` |
| Chain Head | `[HASH_PREFIX]...` |

### Threat Flags Summary

| ID | Threat Class | Severity | OWASP Tags | Event Seq |
|----|--------------|----------|------------|-----------|
| [FLAG_ID] | [CLASS] | [SEV] | [TAGS] | [SEQ] |

---

## Technical Details

### Hash Algorithm
- **Event Hash:** SHA256 with domain prefix `aak:v0:event:`
- **Chain Hash:** SHA256 with domain prefix `aak:v0:chain:`
- **Canonicalization:** RFC 8785 (deterministic JSON)

### Event Hash Contract
```
event_hash = SHA256("aak:v0:event:" + canonical_json(event_payload))
```
- Envelope fields (seq, hash, prev_hash, payload_file) are NOT included
- Only the event payload is hashed

### Chain Integrity
```
chain_link[n] = SHA256("aak:v0:chain:" + prev_hash + ":" + event_hash)
```
- Genesis hash: `SHA256("aak:v0:genesis")`
- Any modification to any event breaks the chain

---

## Retention and Custody

### Recommended Retention Period
- Minimum: 1 year
- Recommended: 3-7 years (align with audit/legal requirements)

### Storage Requirements
- WORM-compatible storage recommended
- Maintain hash verification log
- Document all access

### Chain of Custody Log

| Date | Action | Performed By | Verification |
|------|--------|--------------|--------------|
| [DATE] | Bundle created | [ASSESSOR] | verify.py PASS |
| [DATE] | Bundle transferred | [ASSESSOR] | verify.py PASS |
| [DATE] | Bundle received | [CLIENT] | verify.py [RESULT] |

---

## Support Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| Technical Questions | [CONTACT] | [HOURS] |
| Report Clarification | [CONTACT] | [HOURS] |
| Verification Issues | [CONTACT] | [HOURS] |

---

## Acceptance

By signing below, the recipient acknowledges:
1. Receipt of the evidence pack
2. Understanding of the non-claims statement
3. Successful verification of bundle integrity
4. Responsibility for secure storage and custody

| | Assessor | Client |
|---|----------|--------|
| Name | _________________ | _________________ |
| Title | _________________ | _________________ |
| Date | _________________ | _________________ |
| Signature | _________________ | _________________ |
| Verification Result | PASS | _________________ |

---

*Generated with Agent Audit Kit v[VERSION]*
