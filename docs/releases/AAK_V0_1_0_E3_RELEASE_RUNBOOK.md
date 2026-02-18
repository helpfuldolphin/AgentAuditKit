# AAK v0.1.0-e3 Release Runbook (PowerShell)

```powershell
# 1) Verify working tree and scope
git status --short
git diff --stat

# 2) Quality gates
ruff check src tests                       # expected: All checks passed!
pytest -q                                  # expected: all tests pass

# 3) Cold-run verify zip artifact
Expand-Archive -Path golden_runs\aak-v0.1.0-e3.zip -DestinationPath .\cold_run_release -Force
python -m aak.cli replay verify --bundle .\cold_run_release\bundle    # expected: [OK] Verified 3 events
python -m aak.cli stress run --bundle .\cold_run_release\bundle --profile authority --seed 11 --output .\cold_run_release\stress_verify
# expected stress_run_hash: 700469bdef6020eda02d86115be8ba9e372ae1347837a4b26a924f9287ee8c7d
# expected stress_diff_hash: 8d7fb3e4a308df9264ff31f34834cca8acd60ccd4a8a102b1fbbb27c3ac842bc

# 4) Freeze and publish
git add .
git commit -m "feat(aak): E4 deterministic authority stress + week6 gate + golden run"
git tag aak-v0.1.0-e3
git push && git push --tags
```
