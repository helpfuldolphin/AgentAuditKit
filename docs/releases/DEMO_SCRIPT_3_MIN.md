# 3-Minute Boring Demo Script

## Goal

Show deterministic evidence replay and authority stress verification with no hype.

## Sequence

1. Open GitHub release page for `aak-v0.1.0-e3`.
2. Download `aak-v0.1.0-e3-release.zip`.
3. Unzip into a fresh directory.
4. Run:

```bash
aak replay verify --bundle <unzipped>/bundle
```

Expected: `[OK] Verified 3 events`

5. Run:

```bash
aak stress run --bundle <unzipped>/bundle --profile authority --seed 11
```

Expected hashes:

- `700469bdef6020eda02d86115be8ba9e372ae1347837a4b26a924f9287ee8c7d`
- `8d7fb3e4a308df9264ff31f34834cca8acd60ccd4a8a102b1fbbb27c3ac842bc`

6. Open `bundle/stress_runs/authority/stress_diff.json`.
7. Close with one line:
   "AAK is evidence/replay infrastructure, not a prevention or certification system."
