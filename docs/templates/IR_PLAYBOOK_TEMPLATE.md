# Incident Response Playbook: AI Agent Incidents

**Client:** [CLIENT NAME]
**Version:** [VERSION]
**Last Updated:** [DATE]
**Owner:** [IR TEAM / SECURITY TEAM]

---

## Non-Claims Statement

> **IMPORTANT**: This playbook provides guidance based on heuristic threat detection.
> It is NOT a compliance certification or formal security guarantee.
> Agent Audit Kit produces evidence artifacts for investigation, not prevention.
> Hosted LLMs are non-deterministic; captured behavior may not reproduce exactly.

---

## 1. Preparation

### 1.1 Prerequisites
- [ ] Agent Audit Kit SDK deployed in agent runtime
- [ ] Vault storage configured (local or WORM-compatible)
- [ ] Export pipeline tested
- [ ] IR team trained on bundle verification

### 1.2 Detection Sources
| Source | Description | Priority |
|--------|-------------|----------|
| AAK Threat Flags | Automated heuristic detection | P1 |
| User Reports | End-user reports of unexpected behavior | P2 |
| Monitoring Alerts | Anomaly detection in tool call patterns | P2 |
| Log Analysis | Manual review of agent logs | P3 |

---

## 2. Identification

### 2.1 Threat Classification

| Class | OWASP Tags | Indicators |
|-------|------------|------------|
| **Tool Misuse** | ASI02, ASI03 | Unexpected tool invocation, out-of-scope calls |
| **RAG Poisoning** | ASI01, ASI06 | Injection patterns in retrieved content |
| **Privilege Misuse** | ASI03 | Actions beyond granted permissions |

### 2.2 Initial Triage Checklist
- [ ] Identify affected agent(s) and session(s)
- [ ] Determine time window of incident
- [ ] Assess blast radius (users, data, systems affected)
- [ ] Preserve evidence bundle BEFORE any remediation

---

## 3. Containment

### 3.1 Immediate Actions

**For Tool Misuse:**
```
1. Revoke agent's tool permissions
2. Block specific tool endpoint if possible
3. Enable enhanced logging
```

**For RAG Poisoning:**
```
1. Quarantine affected knowledge base chunks
2. Disable retrieval pipeline temporarily
3. Review recent KB updates/ingestions
```

**For Privilege Misuse:**
```
1. Rotate agent credentials
2. Reduce permission scope
3. Enable strict identity verification
```

### 3.2 Evidence Preservation

```bash
# 1. Export bundle immediately
aak export [RUN_ID] --output ./incident_[TICKET_ID]/

# 2. Verify bundle integrity
cd ./incident_[TICKET_ID]/bundle
python verify.py

# 3. Create read-only backup
cp -r ./bundle ./bundle_readonly
chmod -R 444 ./bundle_readonly
```

---

## 4. Eradication

### 4.1 Root Cause Analysis

**Questions to Answer:**
1. What triggered the malicious behavior?
2. Was it prompt injection, data poisoning, or configuration error?
3. What was the attack vector (user input, RAG content, tool output)?

**Using Evidence Bundle:**
```bash
# Examine specific event
cat events/[SEQ]_[TYPE].json | python -m json.tool

# Check for injection patterns in tool results
grep -r "SYSTEM:" events/
grep -r "ignore" events/

# Review permission context
grep -r "permissions" events/
```

### 4.2 Remediation Steps

| Finding | Remediation | Owner | ETA |
|---------|-------------|-------|-----|
| [F-001] | [ACTION] | [TEAM] | [DATE] |
| [F-002] | [ACTION] | [TEAM] | [DATE] |

---

## 5. Recovery

### 5.1 Service Restoration Checklist
- [ ] Verify remediation deployed
- [ ] Run validation tests against known-bad scenarios
- [ ] Enable monitoring with enhanced sensitivity
- [ ] Restore normal permissions gradually
- [ ] Confirm business functionality intact

### 5.2 Monitoring Period
- Duration: [72 hours / 1 week]
- Escalation criteria: [Any recurrence of flagged behavior]

---

## 6. Lessons Learned

### 6.1 Post-Incident Review Agenda
1. Timeline reconstruction
2. Detection effectiveness
3. Response time analysis
4. Evidence quality assessment
5. Process improvements

### 6.2 Documentation Requirements
- [ ] Incident report filed
- [ ] Evidence bundle archived (retention: [PERIOD])
- [ ] Playbook updates identified
- [ ] Training needs assessed

---

## Appendix A: Bundle Verification Quick Reference

```bash
# Navigate to bundle
cd [BUNDLE_PATH]

# Run verification
python verify.py

# Expected output for intact bundle:
============================================================
 AGENT AUDIT KIT - Evidence Bundle Verification
============================================================
 Bundle ID:    run_[ID]
 Created:      [TIMESTAMP]
 Event Count:  [N]

 Hash Chain:   [OK] INTACT
 Manifest:     [OK] VALID

 THREAT FLAGS:
   [SEVERITY] [CLASS]: [ASI TAGS]

 Status: EVIDENCE ARTIFACT GENERATED
         (Not a compliance certification)
============================================================
```

---

## Appendix B: Contact Matrix

| Role | Contact | Escalation Time |
|------|---------|-----------------|
| IR Lead | [CONTACT] | Immediate |
| Security Engineering | [CONTACT] | < 30 min |
| Agent Development | [CONTACT] | < 1 hour |
| Legal/Compliance | [CONTACT] | < 4 hours |

---

## Appendix C: Evidence Chain of Custody

| Date/Time | Action | Performed By | Hash Verified |
|-----------|--------|--------------|---------------|
| [DATETIME] | Bundle exported | [NAME] | [YES/NO] |
| [DATETIME] | Bundle transferred | [NAME] | [YES/NO] |
| [DATETIME] | Bundle archived | [NAME] | [YES/NO] |

---

*Generated with Agent Audit Kit v[VERSION]*
