# AAK v0.2.0-psych-context

## What this adds

Optional, evidence-only psych-context linkage for forensic bundles, with strict Lane-B boundaries:

- optional `psych_context` on events (`hash_ref` default, `inline_minimal` optional)
- optional psych metadata in `replay_manifest.json`
- fail-closed verification of referenced psych artifacts (missing/extra/modified => fail)
- deterministic report section: `Psychological Context (Captured/Referenced)`
- optional interceptor provider hook for live context attachment

No authority semantics were added.

## Golden run: CEO-fraud + CAC forensic scenarios

Included artifact pack:

- `golden_runs/aak-v0.2.0-psych-ceo-cac/`

Deterministic hashes:

- `stress_run_hash`: `7721d235c688f9795a11c3ecaf0cfab2f180f39f8f449bf4ce35540083bfadd3`
- `stress_diff_hash`: `28b1d1c22ccdcfe3b6e95296da00a514b808090dfc19eb643ed0563bc4e5b25d`
- `report_hash`: `4c4c503f5b48b29cdecfd1f6de5022c62c19e53ae7252cd4c5504e51c8a78bcb`

## Verify in 5 minutes

```bash
python -m aak.cli replay verify --bundle ./bundle
python -m aak.cli stress run --bundle ./bundle --profile authority --seed 11 --output ./stress_verify
python -m aak.cli report generate --bundle ./bundle --out ./report_verify
cd ./bundle && python verify.py
```

## Non-claims

- Evidence tooling only: capture/replay/stress/report.
- No correctness, safety, compliance, or governance authority claims.
- Psych linkage is reference-only and non-authoritative.
- No deterministic hosted-LLM output reproduction.
