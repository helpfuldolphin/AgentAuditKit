# Design Principles

## Legal Exhibit First

The trace is a legal exhibit, not a debugging tool.

The primary output is a temporal narrative with counterfactual clarity, readable by a non-technical compliance officer explaining an AI failure to a board. Technical evidence is referenced, not embedded.

## Capture Perceived World State

AAK must record what the system believed to be true when it acted, not only what action it took.

Decision-boundary evidence should preserve upstream inputs, context references, confidence signals, missing confidence, accountability metadata, policy version, and reversibility.

## Evidence Only

AAK produces evidence artifacts, not authority.

Bundles may support investigation, insurer review, regulator review, legal discovery, and audit preparation. They may not be treated as correctness proofs, compliance certifications, or trust-class upgrades.

## Fail Closed

Portable evidence must verify fail-closed.

Missing, extra, or modified artifacts should cause verification failure. Replay, report generation, and optional verifier-artifact linkage should preserve this property.

## Readable Before Rich

Chronology beats raw telemetry.

When forced to choose, AAK should prefer a concise temporal narrative, decision-context chain, and counterfactual checklist over adding more opaque JSON output.
