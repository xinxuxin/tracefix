from __future__ import annotations

from tracefix.executor import Executor
from tracefix.types import ExecutionResult
from tracefix.types import VerificationResult


class Verifier:
    """Reruns a candidate patch and compares its failure against the previous run."""

    def __init__(self, executor: Executor) -> None:
        self.executor = executor

    def verify(
        self,
        previous_result: ExecutionResult,
        patched_source: str,
        filename: str,
    ) -> VerificationResult:
        rerun_result = self.executor.run_source(patched_source, filename=filename)

        if rerun_result.succeeded:
            return VerificationResult(
                success=True,
                summary="The patched script executed successfully.",
                failure_kind="resolved",
                execution_result=rerun_result,
            )

        if rerun_result.failure_signature == previous_result.failure_signature:
            return VerificationResult(
                success=False,
                summary="The patched script reproduced the same failure signature.",
                failure_kind="same_failure",
                execution_result=rerun_result,
            )

        return VerificationResult(
            success=False,
            summary="The patched script failed differently after the attempted fix.",
            failure_kind="new_failure",
            execution_result=rerun_result,
        )
