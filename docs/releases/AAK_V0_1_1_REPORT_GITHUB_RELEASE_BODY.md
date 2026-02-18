# AAK v0.1.1-report

## What this adds

Deterministic, fail-closed audit report generation on top of existing verified bundles:

- `aak report generate --bundle <path> --out <dir>`
- output: `audit_report.md`
- same bundle bytes => byte-identical report output
- tampered/missing/extra artifacts => report generation fails closed

## Golden run hashes

- `stress_run_hash`: `700469bdef6020eda02d86115be8ba9e372ae1347837a4b26a924f9287ee8c7d`
- `stress_diff_hash`: `8d7fb3e4a308df9264ff31f34834cca8acd60ccd4a8a102b1fbbb27c3ac842bc`
- `report_hash`: `53af62ca77f689aa3ee4bebd3205822f15b7ec7b26bb2c2fc6f183a73f85b85f`

## Verify in 5 minutes

```bash
python -m aak.cli replay verify --bundle ./bundle
python -m aak.cli stress run --bundle ./bundle --profile authority --seed 11 --output ./stress_verify
python -m aak.cli report generate --bundle ./bundle --out ./report_verify
```

## Non-claims

- Evidence tooling only: capture/replay/stress/report.
- No correctness, safety, or compliance claims.
- No intent or causality inference.
- No deterministic hosted-LLM output reproduction.
