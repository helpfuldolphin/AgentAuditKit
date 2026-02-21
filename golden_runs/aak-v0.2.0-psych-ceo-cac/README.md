# AAK Golden Run Evidence Pack (Psych Context v0.2)

Run ID: `run_psychceocac20260221`
AAK Version: `0.1.0`

## Scenario

This deterministic synthetic run includes:
- CEO-fraud style authority + temporal convergence snapshots
- CAC style command-authority-confusion escalation snapshot
- Optional psych context linkage (`hash_ref`)

## Expected Verification

- `python -m aak.cli replay verify --bundle ./bundle` should pass
- `python -m aak.cli stress run --bundle ./bundle --profile authority --seed 11` should pass
- `python -m aak.cli report generate --bundle ./bundle --out ./report_verify` should pass
- `cd ./bundle && python verify.py` should pass

## Deterministic Hashes

- `stress_run_hash`: `7721d235c688f9795a11c3ecaf0cfab2f180f39f8f449bf4ce35540083bfadd3`
- `stress_diff_hash`: `28b1d1c22ccdcfe3b6e95296da00a514b808090dfc19eb643ed0563bc4e5b25d`
- `report_hash`: `4c4c503f5b48b29cdecfd1f6de5022c62c19e53ae7252cd4c5504e51c8a78bcb`

## Non-Claims

- Evidence-only forensic artifact
- No compliance certification
- No governance authority assignment
- No deterministic hosted-LLM output reproduction
