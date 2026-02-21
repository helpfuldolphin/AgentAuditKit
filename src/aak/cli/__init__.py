"""AAK CLI v0.1 command surface."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from aak import __version__
from aak.models.events import EventSource, LLMRequestEvent, LLMResponseEvent, SessionStartEvent
from aak.replay import verify_bundle
from aak.report import ReportError, generate_audit_report
from aak.stress import SUPPORTED_STRESS_PROFILES, StressError, run_stress
from aak.vault.export import export_bundle
from aak.vault.store import VaultWriter

EXIT_OK = 0
EXIT_VERIFY_FAIL = 1
EXIT_USAGE_OR_RUNTIME = 2

NON_CLAIMS = (
    "AAK produces evidence artifacts for investigation. It does not provide compliance "
    "certification, governance authority, or deterministic hosted-LLM output reproduction."
)

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aak",
        description=(
            "Agent Audit Kit CLI. Lane B forensic tooling only. "
            f"{NON_CLAIMS}"
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    commands = parser.add_subparsers(dest="command")

    capture = commands.add_parser("capture", help="Capture and export a run")
    capture_sub = capture.add_subparsers(dest="capture_command")
    capture_run = capture_sub.add_parser(
        "run",
        help="Create a capture run from a declared runtime config",
        description=f"Capture run command. {NON_CLAIMS}",
    )
    capture_run.add_argument("--config", required=True, help="Path to runtime config file")
    capture_run.add_argument("--out", required=True, help="Output directory for vault and bundle")
    capture_run.set_defaults(handler=_handle_capture_run)

    replay = commands.add_parser("replay", help="Replay and verify bundles")
    replay_sub = replay.add_subparsers(dest="replay_command")
    replay_verify = replay_sub.add_parser(
        "verify",
        help="Verify bundle hash-chain integrity",
        description=f"Replay verification command. {NON_CLAIMS}",
    )
    replay_verify.add_argument("--bundle", required=True, help="Path to bundle directory")
    replay_verify.set_defaults(handler=_handle_replay_verify)

    stress = commands.add_parser("stress", help="Run baseline stress profiles")
    stress_sub = stress.add_subparsers(dest="stress_command")
    stress_run = stress_sub.add_parser(
        "run",
        help="Run a stress profile against a verified bundle",
        description=f"Stress command. {NON_CLAIMS}",
    )
    stress_run.add_argument("--bundle", required=True, help="Path to bundle directory")
    stress_run.add_argument(
        "--profile",
        required=True,
        choices=list(SUPPORTED_STRESS_PROFILES),
        help="Stress profile",
    )
    stress_run.add_argument("--seed", type=int, default=0, help="Deterministic seed metadata")
    stress_run.add_argument(
        "--output",
        help="Output directory for stress artifacts (default: <bundle>/stress_runs/<profile>)",
    )
    stress_run.set_defaults(handler=_handle_stress_run)

    report = commands.add_parser("report", help="Generate deterministic audit report artifacts")
    report_sub = report.add_subparsers(dest="report_command")
    report_generate = report_sub.add_parser(
        "generate",
        help="Generate deterministic narrative report from a verified bundle",
        description=f"Report command. {NON_CLAIMS}",
    )
    report_generate.add_argument("--bundle", required=True, help="Path to bundle directory")
    report_generate.add_argument(
        "--out",
        required=True,
        help="Output directory for report artifact",
    )
    report_generate.set_defaults(handler=_handle_report_generate)

    return parser


def _handle_capture_run(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        return EXIT_USAGE_OR_RUNTIME

    output_path = Path(args.out)
    vault_path = output_path / "vault"
    bundle_path = output_path / "bundle"
    output_path.mkdir(parents=True, exist_ok=True)

    writer = VaultWriter(vault_path)
    writer.append_event(
        SessionStartEvent(
            run_id=writer.run_id,
            sdk_version=__version__,
            vault_path=str(vault_path),
            source=EventSource.CAPTURED,
        )
    )
    request_event = LLMRequestEvent(
        model_id="declared-runtime",
        messages=[
            {"role": "system", "content": "Capture scaffold event"},
            {"role": "user", "content": f"Config declared at {config_path.name}"},
        ],
        temperature=0.0,
        provider="aak",
        source=EventSource.CAPTURED,
    )
    req_envelope = writer.append_event(request_event)
    writer.append_event(
        LLMResponseEvent(
            model_id="declared-runtime",
            content="Capture scaffold response",
            finish_reason="stop",
            request_hash=req_envelope.hash,
            provider_request_id=f"capture-{writer.run_id}",
            source=EventSource.CAPTURED,
        )
    )
    writer.finalize()

    result = export_bundle(vault_path, bundle_path, include_verify_script=True)
    print(f"[OK] Capture complete. Bundle: {result.bundle_path}")
    print(f"[OK] Events: {result.event_count}")
    return EXIT_OK


def _handle_replay_verify(args: argparse.Namespace) -> int:
    bundle_path = Path(args.bundle)
    result = verify_bundle(bundle_path)
    if result.valid:
        print(f"[OK] {result.message}")
        return EXIT_OK
    print(f"[FAIL] {result.message}")
    return EXIT_VERIFY_FAIL


def _handle_stress_run(args: argparse.Namespace) -> int:
    try:
        result = run_stress(
            Path(args.bundle),
            profile=args.profile,
            seed=int(args.seed),
            output_dir=args.output,
        )
    except StressError as exc:
        print(f"[FAIL] Stress run failed: {exc}")
        return EXIT_VERIFY_FAIL

    print(f"[OK] Stress run complete. Profile: {result.profile}")
    print(f"[OK] Findings: {result.finding_count}")
    print(f"[OK] Stress bundle: {result.output_dir}")
    print(f"[OK] stress_run_hash: {result.run_hash}")
    print(f"[OK] stress_diff_hash: {result.diff_hash}")
    return EXIT_OK


def _handle_report_generate(args: argparse.Namespace) -> int:
    try:
        result = generate_audit_report(Path(args.bundle), out_dir=Path(args.out))
    except ReportError as exc:
        print(f"[FAIL] Report generation failed: {exc}")
        return EXIT_VERIFY_FAIL

    print("[OK] Report generation complete.")
    print(f"[OK] Bundle ID: {result.bundle_id}")
    print(f"[OK] Events summarized: {result.event_count}")
    print(f"[OK] Decision points: {result.decision_point_count}")
    print(f"[OK] Psych contexts: {result.psych_context_count}")
    print(f"[OK] Report path: {result.report_path}")
    print(f"[OK] report_hash: {result.report_hash}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return EXIT_USAGE_OR_RUNTIME

    try:
        return int(handler(args))
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return EXIT_USAGE_OR_RUNTIME
