from __future__ import annotations

import difflib

from tracefix.types import PatchChangedRegion


def compute_unified_diff(
    original_code: str,
    updated_code: str,
    *,
    fromfile: str = "before.py",
    tofile: str = "after.py",
) -> str:
    """Return a readable unified diff for the patch artifact."""

    diff = difflib.unified_diff(
        original_code.splitlines(keepends=True),
        updated_code.splitlines(keepends=True),
        fromfile=fromfile,
        tofile=tofile,
    )
    return "".join(diff)


def compute_changed_regions(original_code: str, updated_code: str) -> list[PatchChangedRegion]:
    """Return localized before/after regions touched by the patch."""

    original_lines = original_code.splitlines()
    updated_lines = updated_code.splitlines()
    matcher = difflib.SequenceMatcher(a=original_lines, b=updated_lines)
    regions: list[PatchChangedRegion] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        start_line = i1 + 1 if i1 < len(original_lines) else max(1, i1)
        end_line = max(start_line, i2 if i2 > 0 else start_line)
        regions.append(
            PatchChangedRegion(
                start_line=start_line,
                end_line=end_line,
                original_snippet="\n".join(original_lines[i1:i2]),
                updated_snippet="\n".join(updated_lines[j1:j2]),
            )
        )

    return regions
