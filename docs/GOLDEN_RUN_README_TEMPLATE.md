# Golden Run Evidence Pack

Run ID: `[RUN_ID]`  
AAK Version: `[VERSION]`  
Generated On: `[UTC TIMESTAMP]`

## Commands Used

```bash
# 1) Capture
aak capture run --config ./aak.yaml --out ./golden_run

# 2) Replay verification
aak replay verify --bundle ./golden_run/bundle

# 3) Stress (authority profile)
aak stress run --bundle ./golden_run/bundle --profile authority --seed 11
```

## Expected Outputs

- Capture:
  - `[OK] Capture complete. Bundle: ...`
  - `[OK] Events: ...`
- Replay verify:
  - `[OK] Verified ... events`
- Stress:
  - `[OK] Stress run complete. Profile: authority`
  - `[OK] stress_run_hash: ...`
  - `[OK] stress_diff_hash: ...`

## Expected Files

In `./golden_run/bundle/`:

- `replay_manifest.json`
- `events/*.json`
- `verify.py`
- `README.txt`
- `stress_runs/authority/stress_run.json`
- `stress_runs/authority/stress_diff.json`

## Offline Verification

```bash
cd ./golden_run/bundle
python verify.py
```

Expected:

- `Hash Chain: [OK] INTACT`
- `Manifest: [OK] VALID`

## What This Proves

- AAK captured and exported a tamper-evident bundle.
- Bundle verification can be performed independently.
- Stress run produced deterministic artifacts for the selected profile.

## What This Does NOT Prove

- Compliance certification
- Governance authority assignment
- Deterministic hosted-LLM output reproduction
- Safety or correctness guarantees
