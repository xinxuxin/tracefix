from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PolicyDecision:
    """Structured decision describing whether execution is allowed."""

    allowed: bool
    label: str
    reason: str
    notes: list[str]


class SandboxPolicy:
    """A narrow policy gate for course-safe bounded execution."""

    BLOCKED_PATTERNS: tuple[tuple[str, str], ...] = (
        (r"(^|\n)\s*import\s+socket\b", "Network access is out of scope for TraceFix."),
        (r"(^|\n)\s*from\s+socket\s+import\b", "Network access is out of scope for TraceFix."),
        (r"(^|\n)\s*import\s+subprocess\b", "Shell and subprocess spawning are blocked."),
        (r"(^|\n)\s*from\s+subprocess\s+import\b", "Shell and subprocess spawning are blocked."),
        (r"\bos\.system\s*\(", "Shell execution is blocked by policy."),
        (r"\bos\.popen\s*\(", "Shell execution is blocked by policy."),
        (r"\burllib\.request\b", "Network fetches are blocked by policy."),
        (r"(^|\n)\s*import\s+requests\b", "Third-party network fetches are blocked by policy."),
        (r"(^|\n)\s*from\s+requests\s+import\b", "Third-party network fetches are blocked by policy."),
    )

    def evaluate(self, code: str) -> PolicyDecision:
        notes: list[str] = []
        for pattern, reason in self.BLOCKED_PATTERNS:
            if re.search(pattern, code):
                notes.append(reason)
                return PolicyDecision(
                    allowed=False,
                    label="blocked_by_policy",
                    reason=reason,
                    notes=notes,
                )

        return PolicyDecision(
            allowed=True,
            label="allowed",
            reason="Execution is allowed within the current prototype policy.",
            notes=notes,
        )
