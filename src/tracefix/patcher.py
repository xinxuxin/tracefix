from __future__ import annotations

import re

from tracefix.types import Diagnosis
from tracefix.types import PatchCandidate


class Patcher:
    """Generates one conservative patch from a supported diagnosis."""

    def generate(self, source: str, diagnosis: Diagnosis) -> PatchCandidate | None:
        if not diagnosis.supported:
            return None

        if diagnosis.bug_class == "missing_colon":
            return self._patch_missing_colon(source, diagnosis)

        if diagnosis.bug_class == "name_error_typo":
            return self._patch_name_error_typo(source, diagnosis)

        return None

    def _patch_missing_colon(
        self, source: str, diagnosis: Diagnosis
    ) -> PatchCandidate | None:
        if diagnosis.line_number is None:
            return None

        lines = source.splitlines()
        index = diagnosis.line_number - 1
        if index < 0 or index >= len(lines):
            return None

        if lines[index].rstrip().endswith(":"):
            return None

        lines[index] = lines[index].rstrip() + ":"
        return PatchCandidate(
            strategy="append_missing_colon",
            rationale="The diagnoser found a supported block-opening line without a trailing colon.",
            patched_source="\n".join(lines) + "\n",
            changed_lines=[diagnosis.line_number],
        )

    def _patch_name_error_typo(
        self, source: str, diagnosis: Diagnosis
    ) -> PatchCandidate | None:
        if not diagnosis.target_name or not diagnosis.replacement_name:
            return None

        pattern = rf"\b{re.escape(diagnosis.target_name)}\b"
        patched_source, replacements = re.subn(
            pattern,
            diagnosis.replacement_name,
            source,
        )
        if replacements == 0:
            return None

        changed_lines: list[int] = []
        for line_number, line in enumerate(source.splitlines(), start=1):
            if re.search(pattern, line):
                changed_lines.append(line_number)

        if not patched_source.endswith("\n"):
            patched_source += "\n"

        return PatchCandidate(
            strategy="rename_undefined_name_to_close_match",
            rationale="The undefined runtime name is replaced with the closest assigned variable name.",
            patched_source=patched_source,
            changed_lines=changed_lines,
        )
