# AAK v0.3.0 - exhibit-grade decision lineage

## What this is

AAK v0.3.0 shifts the product framing from forensic replay alone to exhibit-grade decision lineage for AI agent failures.

This release is built around a simple rule: the trace is a legal exhibit, not a debugging tool. The output is meant to support post-mortem defensibility, regulator review, insurer review, and board-level incident reporting.

## What this adds

- `DecisionContextSnapshot` as a first-class capture surface for the agent's perceived world state at each decision boundary:
  - upstream inputs
  - confidence signals and explicit missing confidence
  - reversibility
  - policy version
  - accountability metadata (`requested_by`, `approved_by`, `environment`)
- Evidence-pack export designed for a non-technical compliance officer:
  - `temporal_narrative.md`
  - `counterfactual_checklist.md`
  - `decision_context_chain.json`
  - `decision_timeline.mmd`
  - copied technical `bundle/`
- Banking pilot workflow:
  - end-to-end AI Decision Exposure Review scenario
  - capture -> verify -> stress -> evidence-pack generation
  - stable canonical golden run under `golden_runs/aak-v0.3.0-bank-decision-exposure/`
- Verifier evidence interface:
  - contract surface for external formal-verification backends
  - motivated by proof artifacts from systems such as [Leanstral](https://mistral.ai/news/leanstral), which Mistral announced on March 16, 2026 as an Apache 2.0 Lean 4 code agent
- Version hygiene:
  - `0.1.0` / `0.2.0` version drift resolved
  - repo, package metadata, artifacts, and docs aligned on `0.3.0`

## Golden run (cold-run verified)

This release includes a canonical banking golden run that verifies on a cold machine:

- `stress_run_hash`: `66d7189e423175a5dc0b7535ef5f0732465f3dc02d4a93b6030ccc854df4c2b2`
- `stress_diff_hash`: `65a96af5894416f00f530cc448277aba1d6a5ffcfe6cff4653a237f8eafb66a4`
- `report_hash`: `21024383109af9bda45785e5285ec3bb558f103a20eb31ae18ad337737c64c53`

## Verify in ~5 minutes

1. Clone the tagged repo and install dependencies:

```bash
git clone --branch aak-v0.3.0 https://github.com/helpfuldolphin/AgentAuditKit.git
cd AgentAuditKit
pip install -e ".[dev]"
```

2. Run:

```bash
python -m aak.cli replay verify --bundle ./golden_runs/aak-v0.3.0-bank-decision-exposure/bundle
python -m aak.cli stress run --bundle ./golden_runs/aak-v0.3.0-bank-decision-exposure/bundle --profile authority --seed 11 --output ./golden_runs/aak-v0.3.0-bank-decision-exposure/stress_verify
python -m aak.cli report generate --bundle ./golden_runs/aak-v0.3.0-bank-decision-exposure/bundle --out ./golden_runs/aak-v0.3.0-bank-decision-exposure/report_verify
cd ./golden_runs/aak-v0.3.0-bank-decision-exposure/bundle && python verify.py
```

Hashes should match the values above.

## Non-claims

- Evidence tooling only.
- No compliance certification.
- No governance authority or trust-class assignment.
- No deterministic hosted-LLM output claim.
- No formal verification results in this release.
- The banking pilot does not perform live LLM calls; the OpenAI wrapper captures real API surfaces, but this lighthouse workflow uses synthetic and seeded scenario data.
- Verifier evidence is a contract surface only in v0.3.0, not a full prover integration.
