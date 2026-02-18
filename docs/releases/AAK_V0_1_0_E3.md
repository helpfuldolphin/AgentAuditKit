# AAK v0.1.0-e3 Freeze Marker

Status: Frozen workspace milestone for E3 replay/verify/stress baseline

## Canonical Golden Run

- Folder: `golden_runs/aak-v0.1.0-e3`
- Archive (release): `golden_runs/aak-v0.1.0-e3-release.zip`
- Archive (legacy): `golden_runs/aak-v0.1.0-e3.zip`
- Command log: `golden_runs/aak-v0.1.0-e3/commands.log`

## Freeze Scope

- Capture CLI contract
- Replay fail-closed verification
- Deterministic replay timeline
- Deterministic stress artifacts (authority profile)

## Tag Command (Run After Commit)

```bash
git tag aak-v0.1.0-e3
```

Rationale:
Tagging should be done after commit so the tag references the exact frozen state.
