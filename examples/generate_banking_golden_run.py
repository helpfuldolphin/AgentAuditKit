#!/usr/bin/env python3
"""Generate deterministic v0.3 banking decision-lineage golden run artifacts."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aak import __version__
from aak.capture import run_capture_from_config
from aak.report import generate_audit_report
from aak.stress import run_stress


DEFAULT_OUTPUT = Path("golden_runs") / "aak-v0.3.0-bank-decision-exposure"


def _frozen_config_lines(run_id: str | None = None) -> list[str]:
    lines = [
        "scenario: banking_decision_exposure",
        "workflow_id: wire_review_demo",
        "workflow_name: Banking Decision Exposure Review",
        "requested_by: treasury_ops_queue",
        "approved_by: dual_control_officer",
        "environment: banking-prod-sim",
        "policy_version: wire_policy_v3",
        "clock_start: 2026-03-20T14:00:00Z",
        "clock_step_seconds: 1",
        "seed: 11",
    ]
    if run_id is not None:
        lines.insert(7, f"run_id: {run_id}")
    return lines


DEFAULT_RUN_ID = "run_" + hashlib.sha256(
    "\n".join(_frozen_config_lines()).encode("utf-8")
).hexdigest()[:16]


def _prepare_dir(path: Path, force: bool) -> None:
    if path.exists():
        if not force:
            raise ValueError(f"Output path already exists: {path}. Use --force to overwrite.")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _write_config(path: Path) -> None:
    path.write_text("\n".join(_frozen_config_lines(DEFAULT_RUN_ID)) + "\n", encoding="utf-8")


def generate(output_root: Path, force: bool) -> None:
    _prepare_dir(output_root, force=force)

    config_path = output_root / "aak.yaml"
    _write_config(config_path)

    capture_result = run_capture_from_config(config_path, output_root)
    stress_result = run_stress(capture_result.bundle_path, profile="authority", seed=11)
    report_result = generate_audit_report(capture_result.bundle_path, out_dir=output_root / "report")

    commands = [
        f"python examples/generate_banking_golden_run.py --out {output_root} --force",
        f"python -m aak.cli replay verify --bundle {capture_result.bundle_path}",
        (
            "python -m aak.cli stress run "
            f"--bundle {capture_result.bundle_path} --profile authority --seed 11"
        ),
        (
            "python -m aak.cli report generate "
            f"--bundle {capture_result.bundle_path} --out {output_root / 'report'}"
        ),
        f"cd {capture_result.bundle_path} && python verify.py",
    ]
    (output_root / "commands.log").write_text("\n".join(commands) + "\n", encoding="utf-8")

    readme = f"""# AAK Golden Run Evidence Pack (v0.3.0)

Run ID: `{DEFAULT_RUN_ID}`
AAK Version: `{__version__}`
Generated: `2026-03-20`

## Positioning

This golden run freezes the v0.3.0 banking decision-lineage workflow:

- exhibit-grade decision lineage
- decision-context capture at each boundary
- deterministic evidence-pack generation
- banking AI Decision Exposure Review lighthouse scenario

## Commands Used (Generation)

```bash
{chr(10).join(commands)}
```

## Cold-Run Verification

```bash
python -m aak.cli replay verify --bundle ./bundle
python -m aak.cli stress run --bundle ./bundle --profile authority --seed 11 --output ./stress_verify
python -m aak.cli report generate --bundle ./bundle --out ./report_verify
cd ./bundle && python verify.py
```

## Expected Hashes

- `stress_run_hash`: `{stress_result.run_hash}`
- `stress_diff_hash`: `{stress_result.diff_hash}`
- `report_hash`: `{report_result.report_hash}`

## What This Includes

- first-class decision context snapshots
- temporal narrative and counterfactual checklist
- technical bundle copy inside the evidence pack
- evidence-only verifier interface surface

## Non-Claims

- Synthetic/seeded banking scenario data only
- No compliance certification
- No hosted-LLM output determinism claim
- No formal verification results in this golden run
"""
    (output_root / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory for generated banking golden run artifacts",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output directory if it exists",
    )
    args = parser.parse_args()
    generate(args.out, force=args.force)


if __name__ == "__main__":
    main()
