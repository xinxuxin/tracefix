from __future__ import annotations

import argparse
from pathlib import Path

from tracefix.config import TraceFixConfig
from tracefix.controller import TraceFixController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tracefix",
        description="Conservative multi-agent style debugging for single-file Python scripts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    debug_parser = subparsers.add_parser("debug", help="Debug a single Python file.")
    debug_parser.add_argument("script_path", help="Path to the Python file to debug.")
    debug_parser.add_argument(
        "--config",
        help="Optional JSON config file with max_attempts, timeout_seconds, trace_dir, and patch_dir.",
    )
    debug_parser.add_argument("--max-attempts", type=int, help="Override retry budget.")
    debug_parser.add_argument("--timeout-seconds", type=int, help="Override execution timeout.")
    debug_parser.add_argument("--trace-dir", help="Override trace output directory.")
    debug_parser.add_argument("--patch-dir", help="Override patch artifact directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "debug":
        parser.error("Only the debug command is currently supported.")

    config = TraceFixConfig.from_env()
    if args.config:
        config = config.merge(TraceFixConfig.from_json(args.config))
    config = config.with_overrides(
        max_attempts=args.max_attempts,
        timeout_seconds=args.timeout_seconds,
        trace_dir=args.trace_dir,
        patch_dir=args.patch_dir,
    )
    controller = TraceFixController(config=config)
    state = controller.debug_file(Path(args.script_path))
    print(_format_summary(state))
    return 0 if state.status == "fixed" else 1

def _format_summary(state) -> str:
    lines = [
        f"session_id: {state.session_id}",
        f"status: {state.status}",
        f"target_file: {state.target_file}",
        f"final_message: {state.final_message}",
        f"trace_path: {state.trace_path}",
    ]
    if state.saved_patch_path:
        lines.append(f"saved_patch_path: {state.saved_patch_path}")
    if state.attempts:
        latest = state.attempts[-1]
        lines.append(f"last_bug_class: {latest.diagnosis.bug_class}")
        if latest.patch_candidate is not None:
            lines.append(f"last_patch_strategy: {latest.patch_candidate.strategy}")
        if latest.verification is not None:
            lines.append(f"last_verification: {latest.verification.failure_kind}")
    return "\n".join(lines)
