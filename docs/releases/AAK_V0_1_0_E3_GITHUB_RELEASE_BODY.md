# AAK v0.1.0-e3 - deterministic capture->replay->stress (authority)

## What this is

AAK v0.1.0-e3 is an open-core evidence toolkit for agents: deterministic capture -> replay verify -> stress (authority). It produces portable evidence bundles and fail-closed verification.

## Golden run (cold-run verified)

This release includes a canonical "golden run" zip that verifies on a cold machine:

- `stress_run_hash`: `700469bdef6020eda02d86115be8ba9e372ae1347837a4b26a924f9287ee8c7d`
- `stress_diff_hash`: `8d7fb3e4a308df9264ff31f34834cca8acd60ccd4a8a102b1fbbb27c3ac842bc`

## Verify in ~5 minutes

1. Unzip `aak-v0.1.0-e3-release.zip`
2. Run:

```bash
aak replay verify --bundle <path-to-bundle>
aak stress run --bundle <path-to-bundle> --profile authority --seed 11
```

Hashes should match the values above.

## Non-claims

- Evidence tooling only (capture/replay/stress).
- No compliance certification.
- No claim of determinism for hosted LLM outputs.
- No prevention claims; this is forensic/replay infrastructure.
