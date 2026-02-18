# AAK Golden Run Evidence Pack

Run ID: `run_f1ff76f49bfc60eb`  
AAK Version: `0.1.0`  
Generated: `2026-02-18`

## Commands Used (Generation)

```bash
python -m aak.cli capture run --config golden_runs/aak-v0.1.0-e3/aak.yaml --out golden_runs/aak-v0.1.0-e3
python -m aak.cli replay verify --bundle golden_runs/aak-v0.1.0-e3/bundle
python -m aak.cli stress run --bundle golden_runs/aak-v0.1.0-e3/bundle --profile authority --seed 11
cd golden_runs/aak-v0.1.0-e3/bundle && python verify.py
```

## Commands Used (Cold-Run Verification)

```bash
python -m aak.cli replay verify --bundle ./bundle
python -m aak.cli stress run --bundle ./bundle --profile authority --seed 11 --output ./stress_verify
cd ./bundle && python verify.py
```

## Expected Outputs

- Capture: `[OK] Capture complete` and `[OK] Events: 3`
- Replay verify: `[OK] Verified 3 events`
- Stress: `[OK] Stress run complete. Profile: authority`
- Bundle verify script: `Hash Chain: [OK] INTACT` and `Manifest: [OK] VALID`
- `stress_run_hash`: `700469bdef6020eda02d86115be8ba9e372ae1347837a4b26a924f9287ee8c7d`
- `stress_diff_hash`: `8d7fb3e4a308df9264ff31f34834cca8acd60ccd4a8a102b1fbbb27c3ac842bc`

## Artifact Layout

- `bundle/replay_manifest.json`
- `bundle/events/*.json`
- `bundle/verify.py`
- `bundle/stress_runs/authority/stress_run.json`
- `bundle/stress_runs/authority/stress_diff.json`
- `commands.log`

## What This Proves

- AAK can capture and export a tamper-evident evidence bundle.
- AAK replay verification passes on an intact bundle.
- AAK stress run (authority profile) produces deterministic artifact hashes for this input.

## What This Does Not Prove

- Compliance certification
- Governance authority assignment
- Deterministic hosted-LLM output reproduction
- Model correctness or safety guarantees
