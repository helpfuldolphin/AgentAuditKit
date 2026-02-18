# Publishing Checklist (AAK v0.1.0-e3)

## 1) Auth and Remote

```powershell
git remote -v
gh auth status
```

If `gh auth status` fails:

```powershell
gh auth login -h github.com
```

## 2) Push Frozen State

```powershell
git status --short
git push -u origin master:main
git push --tags
```

Expected:

- `origin/main` points at commit `b474138`
- tag `aak-v0.1.0-e3` exists on same commit

## 3) Create GitHub Release

Tag: `aak-v0.1.0-e3`  
Title: `AAK v0.1.0-e3 - deterministic capture->replay->stress (authority)`  
Asset: `golden_runs/aak-v0.1.0-e3-release.zip`  
Body: `docs/releases/AAK_V0_1_0_E3_GITHUB_RELEASE_BODY.md`

CLI:

```powershell
gh release create aak-v0.1.0-e3 `
  --repo helpfuldolphin/AgentAuditKit `
  --title "AAK v0.1.0-e3 - deterministic capture->replay->stress (authority)" `
  --notes-file docs/releases/AAK_V0_1_0_E3_GITHUB_RELEASE_BODY.md `
  golden_runs/aak-v0.1.0-e3-release.zip
```

## 4) Cold-Run Re-Verification (Release Asset)

```powershell
Expand-Archive -Path .\aak-v0.1.0-e3-release.zip -DestinationPath .\cold_run_verify -Force
aak replay verify --bundle .\cold_run_verify\bundle
aak stress run --bundle .\cold_run_verify\bundle --profile authority --seed 11
```

Expected hashes:

- `stress_run_hash`: `700469bdef6020eda02d86115be8ba9e372ae1347837a4b26a924f9287ee8c7d`
- `stress_diff_hash`: `8d7fb3e4a308df9264ff31f34834cca8acd60ccd4a8a102b1fbbb27c3ac842bc`

## 5) Publish Links

- GitHub release URL (not repo root)
- 3-minute demo video link
- One announcement post using non-claims language
