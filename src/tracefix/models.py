"""Compatibility module for older imports.

The repository now keeps shared data contracts in `tracefix.types`
and session state in `tracefix.state`.
"""

from tracefix.state import SessionState
from tracefix.types import AttemptRecord
from tracefix.types import Diagnosis
from tracefix.types import ExecutionResult
from tracefix.types import PatchCandidate
from tracefix.types import VerificationResult
from tracefix.types import to_dict

__all__ = [
    "AttemptRecord",
    "Diagnosis",
    "ExecutionResult",
    "PatchCandidate",
    "SessionState",
    "VerificationResult",
    "to_dict",
]
