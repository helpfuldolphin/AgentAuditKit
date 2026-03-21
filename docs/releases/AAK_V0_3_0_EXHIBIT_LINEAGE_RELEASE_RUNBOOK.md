# AAK v0.3.0 Exhibit Lineage Release Runbook (PowerShell)

```powershell
# 1) Verify working tree and scope
git status --short
git diff --stat

# 2) Quality gates
ruff check src tests
mypy src
pytest -q

# 3) Re-freeze canonical banking golden run
python examples\generate_banking_golden_run.py --out golden_runs\aak-v0.3.0-bank-decision-exposure --force
python -m aak.cli replay verify --bundle .\golden_runs\aak-v0.3.0-bank-decision-exposure\bundle
python -m aak.cli stress run --bundle .\golden_runs\aak-v0.3.0-bank-decision-exposure\bundle --profile authority --seed 11 --output .\golden_runs\aak-v0.3.0-bank-decision-exposure\stress_verify
python -m aak.cli report generate --bundle .\golden_runs\aak-v0.3.0-bank-decision-exposure\bundle --out .\golden_runs\aak-v0.3.0-bank-decision-exposure\report_verify
cd .\golden_runs\aak-v0.3.0-bank-decision-exposure\bundle; python verify.py; cd ..\..\..
# expected stress_run_hash: 66d7189e423175a5dc0b7535ef5f0732465f3dc02d4a93b6030ccc854df4c2b2
# expected stress_diff_hash: 65a96af5894416f00f530cc448277aba1d6a5ffcfe6cff4653a237f8eafb66a4
# expected report_hash: 21024383109af9bda45785e5285ec3bb558f103a20eb31ae18ad337737c64c53

# 4) Freeze release artifact zip (optional GitHub upload asset)
if (Test-Path golden_runs\aak-v0.3.0-bank-decision-exposure.zip) { Remove-Item -Force golden_runs\aak-v0.3.0-bank-decision-exposure.zip }
Compress-Archive -Path golden_runs\aak-v0.3.0-bank-decision-exposure -DestinationPath golden_runs\aak-v0.3.0-bank-decision-exposure.zip -Force

# 5) Commit, tag, and validate from a fresh clone
git add .
git commit -m "feat(aak): v0.3 exhibit-grade decision lineage"
git tag aak-v0.3.0
git clone . ..\agent-audit-kit-coldrun-v0.3.0
cd ..\agent-audit-kit-coldrun-v0.3.0
git checkout aak-v0.3.0
pip install -e ".[dev]"
python -m aak.cli replay verify --bundle .\golden_runs\aak-v0.3.0-bank-decision-exposure\bundle
python -m aak.cli stress run --bundle .\golden_runs\aak-v0.3.0-bank-decision-exposure\bundle --profile authority --seed 11 --output .\golden_runs\aak-v0.3.0-bank-decision-exposure\stress_verify
python -m aak.cli report generate --bundle .\golden_runs\aak-v0.3.0-bank-decision-exposure\bundle --out .\golden_runs\aak-v0.3.0-bank-decision-exposure\report_verify
cd .\golden_runs\aak-v0.3.0-bank-decision-exposure\bundle; python verify.py
```
