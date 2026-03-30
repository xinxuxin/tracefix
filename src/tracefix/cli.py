from __future__ import annotations

import argparse
from pathlib import Path

from tracefix.config import TraceFixConfig
from tracefix.orchestrator.controller import TraceFixController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tracefix",
        description="Conservative multi-agent debugging for single-file Python scripts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    debug_parser = subparsers.add_parser("debug", help="Debug a single Python file.")
    debug_parser.add_argument("script_path", help="Path to the Python file to debug.")
    debug_parser.add_argument("--config", help="Optional JSON config file.")
    debug_parser.add_argument("--max-retries", type=int, help="Bounded retry budget for patch attempts.")
    debug_parser.add_argument("--timeout-seconds", type=int, help="Override execution timeout.")
    debug_parser.add_argument("--trace-dir", help="Override base trace directory from config.")
    debug_parser.add_argument("--patch-dir", help="Override base patch directory from config.")
    debug_parser.add_argument(
        "--expected-output-file",
        help="Path to a text file containing expected stdout for acceptance checks.",
    )
    debug_parser.add_argument(
        "--expected-output-text",
        help="Inline expected stdout for acceptance checks.",
    )
    debug_parser.add_argument(
        "--session-root",
        help="Directory where per-session artifacts should be written.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "debug":
        parser.error("Only the debug command is currently supported.")

    if args.expected_output_file and args.expected_output_text:
        parser.error("Use only one of --expected-output-file or --expected-output-text.")

    config = TraceFixConfig.from_env()
    if args.config:
        config = config.merge(TraceFixConfig.from_json(args.config))
    config = config.with_overrides(
        max_attempts=args.max_retries,
        timeout_seconds=args.timeout_seconds,
        trace_dir=args.trace_dir,
        patch_dir=args.patch_dir,
    )

    expected_output = _load_expected_output(
        expected_output_file=args.expected_output_file,
        expected_output_text=args.expected_output_text,
    )
    controller = TraceFixController(
        config=config,
        session_root=args.session_root,
    )
    state = controller.debug_file(
        Path(args.script_path),
        expected_output=expected_output,
        max_retries=args.max_retries,
    )
    print(_format_summary(state))
    return 0 if state.final_decision in {"accept"} else 1


def _load_expected_output(
    *,
    expected_output_file: str | None,
    expected_output_text: str | None,
) -> str | None:
    if expected_output_file:
        return Path(expected_output_file).read_text(encoding="utf-8")
    return expected_output_text


def _format_summary(state) -> str:
    lines = [
        f"session_id: {state.session_id}",
        f"status: {state.status}",
        f"final_decision: {state.final_decision}",
        f"target_file: {state.target_file}",
        f"final_message: {state.final_message}",
        f"session_dir: {state.session_dir}",
        f"trace_jsonl: {state.trace_events_path}",
        f"state_snapshot: {state.trace_path}",
        f"summary_markdown: {state.summary_path}",
    ]
    if state.saved_patch_path:
        lines.append(f"accepted_patch: {state.saved_patch_path}")
    if state.failure_summary_path:
        lines.append(f"failure_summary: {state.failure_summary_path}")
    if state.attempt_details:
        last_attempt = state.attempt_details[-1]
        diagnosis = last_attempt.get("diagnosis_result")
        patch_result = last_attempt.get("patch_result")
        verifier_result = last_attempt.get("verifier_result")
        lines.append(
            "last_attempt: "
            f"diagnosis={getattr(diagnosis, 'primary_bug_class', 'n/a')}, "
            f"patch={getattr(patch_result, 'strategy_id', None) or 'refused'}, "
            f"verifier={getattr(verifier_result, 'decision', 'not_run')}"
        )
    return "\n".join(lines)
