from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tracefix.orchestrator.controller import TraceFixController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a demo TraceFix session on a sample case.")
    parser.add_argument(
        "--case",
        default=str(ROOT / "cases" / "name_error_bug.py"),
        help="Path to the demo Python file.",
    )
    parser.add_argument(
        "--expected-output-text",
        default="Hello, TraceFix!\n",
        help="Expected stdout used for verifier acceptance.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Retry budget for patch attempts.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    controller = TraceFixController(max_attempts=args.max_retries)
    state = controller.debug_file(
        args.case,
        expected_output=args.expected_output_text,
        max_retries=args.max_retries,
    )
    print(f"session_id: {state.session_id}")
    print(f"status: {state.status}")
    print(f"final_decision: {state.final_decision}")
    print(f"session_dir: {state.session_dir}")
    print(f"summary_path: {state.summary_path}")
    if state.saved_patch_path:
        print(f"accepted_patch: {state.saved_patch_path}")
    if state.failure_summary_path:
        print(f"failure_summary: {state.failure_summary_path}")
    return 0 if state.final_decision == "accept" else 1


if __name__ == "__main__":
    raise SystemExit(main())
