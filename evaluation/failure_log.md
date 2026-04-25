# Failure and Governance Log

This log is generated from executed TraceFix evaluation cases. It includes unresolved, stopped, and escalated cases rather than invented examples.

## failure_01: bug_case_05_runtime_exception

- **failure_id**: `failure_01`
- **date**: 2026-04-25
- **version_tested**: local deterministic mode · evaluation run `20260425T172418Z`
- **what_triggered_the_problem**: List access raises `IndexError` with no safe bounded patch strategy available.
- **what_happened**: Session ended with `status=stopped_no_patch`, `decision=stop`, and no patch rerun. The Patcher refused because no conservative single-line fix could be justified without guessing user intent about list bounds.
- **severity**: medium — system stopped safely; no incorrect patch was applied
- **fix_attempted**: None. Refusal is the intended behavior. `IndexError` on list access is out-of-scope for bounded local patching.
- **current_status**: Documented boundary case for final submission. Retained as evidence that unsupported runtime cases stop rather than trigger broad speculative edits.
- **evidence artifacts**:
  - `evaluation/runs/20260425T172418Z/cases/bug_case_05_runtime_exception/sessions/bug_case_05_runtime_exception_20260425T172419016859Z/summary.md`
  - `evaluation/runs/20260425T172418Z/cases/bug_case_05_runtime_exception/sessions/bug_case_05_runtime_exception_20260425T172419016859Z/trace.jsonl`
  - `evaluation/runs/20260425T172418Z/cases/bug_case_05_runtime_exception/sessions/bug_case_05_runtime_exception_20260425T172419016859Z/session_state.json`

---

## failure_02: bug_case_06_failure_superficial_fix

- **failure_id**: `failure_02`
- **date**: 2026-04-25
- **version_tested**: local deterministic mode · evaluation run `20260425T172418Z`
- **what_triggered_the_problem**: A variable typo causes a `NameError`. A rename patch removes the crash, but the output (`HELLO, TRACEFIX!`) violates the intended greeting format (`Hello, TraceFix!`).
- **what_happened**: Session ended with `decision=stop`. The Verifier rejected the patch because expected output did not match — crash gone but behavior oracle failed. A second attempt was refused by the Patcher due to low diagnosis confidence.
- **severity**: high — primary false-positive acceptance risk case. A crash-only baseline would have incorrectly accepted this patch.
- **fix_attempted**: No code change needed; system behaved as designed. The Verifier's expected-output oracle is the mechanism that prevents false-positive acceptance.
- **current_status**: Documented failure-analysis case. Retained as the strongest evidence that TraceFix does not equate "no crash" with "correct behavior."
- **evidence artifacts**:
  - `evaluation/runs/20260425T172418Z/cases/bug_case_06_failure_superficial_fix/sessions/bug_case_06_failure_superficial_fix_20260425T172419048519Z/summary.md`
  - `evaluation/runs/20260425T172418Z/cases/bug_case_06_failure_superficial_fix/sessions/bug_case_06_failure_superficial_fix_20260425T172419048519Z/trace.jsonl`
  - `evaluation/runs/20260425T172418Z/cases/bug_case_06_failure_superficial_fix/sessions/bug_case_06_failure_superficial_fix_20260425T172419048519Z/patches/attempt_01.diff`

---

## failure_03: bug_case_07_failure_ambiguous_behavior

- **failure_id**: `failure_03`
- **date**: 2026-04-25
- **version_tested**: local deterministic mode · evaluation run `20260425T172418Z`
- **what_triggered_the_problem**: A variable typo causes a `NameError`. A rename patch removes the crash and prints `17`, but no expected output was supplied so there is no behavior oracle.
- **what_happened**: Session ended with `decision=escalate`. The Verifier escalated for human review rather than auto-accepting because it could not confirm `17` was the intended output.
- **severity**: medium — system escalated correctly; no incorrect patch was persisted.
- **fix_attempted**: None. Escalation is the intended governance behavior for no-oracle cases. Root cause is the absence of a user-supplied expected output.
- **current_status**: Documented governance case. Retained as evidence that TraceFix escalates no-oracle success rather than accepting it by default.
- **evidence artifacts**:
  - `evaluation/runs/20260425T172418Z/cases/bug_case_07_failure_ambiguous_behavior/sessions/bug_case_07_failure_ambiguous_behavior_20260425T172419111520Z/summary.md`
  - `evaluation/runs/20260425T172418Z/cases/bug_case_07_failure_ambiguous_behavior/sessions/bug_case_07_failure_ambiguous_behavior_20260425T172419111520Z/trace.jsonl`
  - `evaluation/runs/20260425T172418Z/cases/bug_case_07_failure_ambiguous_behavior/sessions/bug_case_07_failure_ambiguous_behavior_20260425T172419111520Z/patches/attempt_01.diff`
