# AAK Golden Run Evidence Pack (v0.3.0)

Run ID: `run_36739dd5b370869b`
AAK Version: `0.3.0`
Generated: `2026-03-20`

## Positioning

This golden run freezes the v0.3.0 banking decision-lineage workflow:

- exhibit-grade decision lineage
- decision-context capture at each boundary
- deterministic evidence-pack generation
- banking AI Decision Exposure Review lighthouse scenario

## Commands Used (Generation)

```bash
python examples/generate_banking_golden_run.py --out golden_runs\aak-v0.3.0-bank-decision-exposure --force
python -m aak.cli replay verify --bundle golden_runs\aak-v0.3.0-bank-decision-exposure\bundle
python -m aak.cli stress run --bundle golden_runs\aak-v0.3.0-bank-decision-exposure\bundle --profile authority --seed 11
python -m aak.cli report generate --bundle golden_runs\aak-v0.3.0-bank-decision-exposure\bundle --out golden_runs\aak-v0.3.0-bank-decision-exposure\report
cd golden_runs\aak-v0.3.0-bank-decision-exposure\bundle && python verify.py
```

## Cold-Run Verification

```bash
python -m aak.cli replay verify --bundle ./bundle
python -m aak.cli stress run --bundle ./bundle --profile authority --seed 11 --output ./stress_verify
python -m aak.cli report generate --bundle ./bundle --out ./report_verify
cd ./bundle && python verify.py
```

## Expected Hashes

- `stress_run_hash`: `66d7189e423175a5dc0b7535ef5f0732465f3dc02d4a93b6030ccc854df4c2b2`
- `stress_diff_hash`: `65a96af5894416f00f530cc448277aba1d6a5ffcfe6cff4653a237f8eafb66a4`
- `report_hash`: `21024383109af9bda45785e5285ec3bb558f103a20eb31ae18ad337737c64c53`

## What This Includes

- first-class decision context snapshots
- temporal narrative and counterfactual checklist
- technical bundle copy inside the evidence pack
- evidence-only verifier interface surface

## Non-Claims

- Synthetic/seeded banking scenario data only
- No compliance certification
- No hosted-LLM output determinism claim
- No formal verification results in this golden run
