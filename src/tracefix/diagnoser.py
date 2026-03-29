from __future__ import annotations

import ast
import difflib
import re
from dataclasses import dataclass

from tracefix.types import Diagnosis
from tracefix.types import ExecutionResult


@dataclass
class _AssignedNameCollector(ast.NodeVisitor):
    names: set[str]

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self.names.add(node.id)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        self.names.add(node.arg)


class Diagnoser:
    """Maps an execution failure into a supported diagnosis or a stop condition."""

    CONTROL_PREFIXES = (
        "if ",
        "elif ",
        "else",
        "for ",
        "while ",
        "def ",
        "class ",
        "try",
        "except",
        "with ",
    )

    def diagnose(self, source: str, result: ExecutionResult) -> Diagnosis:
        if result.succeeded:
            return Diagnosis(
                supported=False,
                bug_class="no_failure",
                summary="The script executed successfully.",
                evidence=["The executor returned exit code 0."],
                confidence=1.0,
                stop_reason="no_failure_detected",
            )

        if result.exception_type == "SyntaxError":
            diagnosis = self._diagnose_missing_colon(source, result)
            if diagnosis is not None:
                return diagnosis

        if result.exception_type == "NameError":
            diagnosis = self._diagnose_name_error_typo(source, result)
            if diagnosis is not None:
                return diagnosis

        return Diagnosis(
            supported=False,
            bug_class="unsupported_failure",
            summary="The failure pattern is outside the current prototype scope.",
            evidence=[
                f"Observed exception type: {result.exception_type or 'unknown'}",
                f"Observed exception message: {result.exception_message or ''}",
            ],
            confidence=0.2,
            stop_reason="unsupported_failure",
        )

    def _diagnose_missing_colon(
        self, source: str, result: ExecutionResult
    ) -> Diagnosis | None:
        if result.failure_line is None:
            return None

        if result.exception_message not in {"expected ':'", "invalid syntax"}:
            return None

        lines = source.splitlines()
        if result.failure_line < 1 or result.failure_line > len(lines):
            return None

        raw_line = lines[result.failure_line - 1]
        stripped = raw_line.strip()
        if not stripped or stripped.endswith(":"):
            return None

        if not stripped.startswith(self.CONTROL_PREFIXES):
            return None

        return Diagnosis(
            supported=True,
            bug_class="missing_colon",
            summary="A block-opening line appears to be missing a trailing colon.",
            evidence=[
                f"Python reported SyntaxError: {result.exception_message}.",
                f"Line {result.failure_line} starts with a supported block keyword.",
            ],
            confidence=0.95,
            line_number=result.failure_line,
        )

    def _diagnose_name_error_typo(
        self, source: str, result: ExecutionResult
    ) -> Diagnosis | None:
        if not result.exception_message:
            return None

        match = re.search(r"name '([A-Za-z_][A-Za-z0-9_]*)' is not defined", result.exception_message)
        if not match:
            return None

        missing_name = match.group(1)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        collector = _AssignedNameCollector(names=set())
        collector.visit(tree)
        candidates = sorted(name for name in collector.names if name != missing_name)
        closest = difflib.get_close_matches(missing_name, candidates, n=1, cutoff=0.75)
        if not closest:
            return None

        replacement = closest[0]
        return Diagnosis(
            supported=True,
            bug_class="name_error_typo",
            summary="The undefined name closely matches an existing assigned variable.",
            evidence=[
                f"Undefined name: {missing_name}",
                f"Closest assigned name: {replacement}",
            ],
            confidence=0.88,
            target_name=missing_name,
            replacement_name=replacement,
        )
