# Evaluation Cases

This file defines the current course-facing evaluation set for TraceFix. It is aligned with the implemented controller, verifier, and evaluation runner.

## Core Evaluation Cases

| case_id | file | case_type | input_or_scenario | expected_behavior | ideal system action | judgment rule |
| --- | --- | --- | --- | --- | --- | --- |
| `bug_case_01_syntax_error` | `cases/bug_case_01_syntax_error.py` | syntax error | Function definition is missing a trailing colon. | Print `A` | `accept` | Accepted patch, expected output matched, and patch is localized. |
| `bug_case_02_name_error` | `cases/bug_case_02_name_error.py` | name error | Runtime variable typo inside a formatted total. | Print `10.70` | `accept` | Accepted patch, expected output matched, and original failure resolved. |
| `bug_case_03_argument_mismatch` | `cases/bug_case_03_argument_mismatch.py` | argument mismatch | Function is called with one extra positional argument. | Print `TRACEFIX READY` | `accept` | Accepted patch, expected output matched, and retry count stays bounded. |
| `bug_case_04_missing_file` | `cases/bug_case_04_missing_file.py` | missing file/resource | Script tries to read `username.txt`, which is absent. | Print `Guest` | `accept` | Accepted patch, expected output matched, and fix remains conservative. |
| `bug_case_05_runtime_exception` | `cases/bug_case_05_runtime_exception.py` | unsupported runtime exception | List access raises `IndexError` with no safe patch strategy in scope. | Stop conservatively without over-editing. | `stop` | No accepted patch, explicit failure summary, and refusal is explainable. |

## Explicit Failure / Governance Cases

| case_id | file | case_type | input_or_scenario | expected_behavior | ideal system action | judgment rule |
| --- | --- | --- | --- | --- | --- | --- |
| `bug_case_06_failure_superficial_fix` | `cases/bug_case_06_failure_superficial_fix.py` | superficial fix failure | A rename removes the original crash, but the remaining output still violates the intended greeting behavior. | Print `Hello, TraceFix!` | `stop` | The verifier should reject superficial success and the session should remain unresolved. |
| `bug_case_07_failure_ambiguous_behavior` | `cases/bug_case_07_failure_ambiguous_behavior.py` | ambiguous behavior failure | A rename can remove the crash, but no expected-output oracle is supplied. | Do not auto-accept without stronger behavioral evidence. | `escalate` | The session should escalate because successful execution alone is insufficient evidence. |

## Why These Cases Matter

- Cases `01` to `04` show that TraceFix can perform bounded, auditable repairs across multiple beginner-friendly bug classes.
- Case `05` shows conservative refusal instead of unsafe overreach.
- Case `06` shows why “the crash went away” is not enough for acceptance.
- Case `07` shows why the verifier is a separate governance component and why ambiguity leads to escalation.

## Current Success Criteria

The current prototype is behaving as intended when:

1. Each case produces a per-session trace and summary.
2. Repairable cases are accepted only when the verifier has enough evidence.
3. Failure cases produce explicit `stop` or `escalate` outcomes instead of silent over-claiming.
4. The evaluation runner records measurable outputs such as retry count, latency, patch breadth, failure resolution status, and behavior match status.
