# Failure and Governance Log

This log is generated from executed TraceFix evaluation cases. It includes unresolved, stopped, and escalated cases rather than invented examples.

## failure_01: bug_case_05_runtime_exception

- Failure ID: `failure_01`
- Case ID: `bug_case_05_runtime_exception`
- What triggered the problem: List access raises IndexError with no safe bounded patch strategy.
- Expected behavior: Stop conservatively instead of over-editing.
- Actual behavior: Session ended with status=stopped_no_patch, decision=stop, and no patch rerun.
- System decision: `stop`
- Why verifier accepted/rejected/escalated/stopped: No accepted patch and explicit stop recorded.
- Root cause: Primary unsupported runtime case.
- Evidence artifacts: `evaluation/runs/20260425T180442Z/cases/bug_case_05_runtime_exception/sessions/bug_case_05_runtime_exception_20260426T051839543444Z/summary.md`, `evaluation/runs/20260425T180442Z/cases/bug_case_05_runtime_exception/sessions/bug_case_05_runtime_exception_20260426T051839543444Z/trace.jsonl`, `evaluation/runs/20260425T180442Z/cases/bug_case_05_runtime_exception/sessions/bug_case_05_runtime_exception_20260426T051839543444Z/session_state.json`
- What changed after testing: The case was retained as evidence for conservative stopping/escalation and documented in Phase 3 materials.
- Current status: Documented boundary case for final submission.

## failure_02: bug_case_06_failure_superficial_fix

- Failure ID: `failure_02`
- Case ID: `bug_case_06_failure_superficial_fix`
- What triggered the problem: A rename removes the crash, but the remaining output still violates the intended greeting format.
- Expected behavior: Print Hello, TraceFix!
- Actual behavior: Session ended with decision=stop; latest rerun outcome=normal_completion; stdout='HELLO, TRACEFIX!'.
- System decision: `stop`
- Why verifier accepted/rejected/escalated/stopped: Verifier should reject superficial success and session should remain unresolved.
- Root cause: Best failure-analysis case for false-positive acceptance risk.
- Evidence artifacts: `evaluation/runs/20260425T180442Z/cases/bug_case_06_failure_superficial_fix/sessions/bug_case_06_failure_superficial_fix_20260426T051839578014Z/summary.md`, `evaluation/runs/20260425T180442Z/cases/bug_case_06_failure_superficial_fix/sessions/bug_case_06_failure_superficial_fix_20260426T051839578014Z/trace.jsonl`, `evaluation/runs/20260425T180442Z/cases/bug_case_06_failure_superficial_fix/sessions/bug_case_06_failure_superficial_fix_20260426T051839578014Z/session_state.json`
- What changed after testing: The case was retained as evidence for conservative stopping/escalation and documented in Phase 3 materials.
- Current status: Documented boundary case for final submission.

## failure_03: bug_case_07_failure_ambiguous_behavior

- Failure ID: `failure_03`
- Case ID: `bug_case_07_failure_ambiguous_behavior`
- What triggered the problem: A rename can remove the crash, but no expected output is supplied to verify the intended behavior.
- Expected behavior: Do not auto-accept without an explicit oracle.
- Actual behavior: Session ended with decision=escalate; latest rerun outcome=normal_completion; stdout='17'.
- System decision: `escalate`
- Why verifier accepted/rejected/escalated/stopped: Escalated session with no behavior oracle.
- Root cause: Best governance and ambiguity case.
- Evidence artifacts: `evaluation/runs/20260425T180442Z/cases/bug_case_07_failure_ambiguous_behavior/sessions/bug_case_07_failure_ambiguous_behavior_20260426T051839642836Z/summary.md`, `evaluation/runs/20260425T180442Z/cases/bug_case_07_failure_ambiguous_behavior/sessions/bug_case_07_failure_ambiguous_behavior_20260426T051839642836Z/trace.jsonl`, `evaluation/runs/20260425T180442Z/cases/bug_case_07_failure_ambiguous_behavior/sessions/bug_case_07_failure_ambiguous_behavior_20260426T051839642836Z/session_state.json`
- What changed after testing: The case was retained as evidence for conservative stopping/escalation and documented in Phase 3 materials.
- Current status: Documented boundary case for final submission.
