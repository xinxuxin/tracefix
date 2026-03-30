# TraceFix Evaluation Cases

This directory contains course-ready single-file debugging scenarios for TraceFix.

## Case Catalog

| case_id | file | case_type | expected_behavior | ideal system action | judgment rule |
| --- | --- | --- | --- | --- | --- |
| `bug_case_01_syntax_error` | `bug_case_01_syntax_error.py` | syntax error | print `A` | accept a minimal colon fix | accepted patch, expected output matched |
| `bug_case_02_name_error` | `bug_case_02_name_error.py` | name error | print `10.70` | accept a localized variable rename | accepted patch, expected output matched |
| `bug_case_03_argument_mismatch` | `bug_case_03_argument_mismatch.py` | argument mismatch | print `TRACEFIX READY` | accept a bounded call-site repair | accepted patch, expected output matched |
| `bug_case_04_missing_file` | `bug_case_04_missing_file.py` | missing file/resource | print `Guest` | accept a conservative file-read guard | accepted patch, expected output matched |
| `bug_case_05_runtime_exception` | `bug_case_05_runtime_exception.py` | unsupported runtime exception | stop without unsafe patching | stop and write failure summary | no accepted patch, explicit stop recorded |
| `bug_case_06_failure_superficial_fix` | `bug_case_06_failure_superficial_fix.py` | failure: superficial fix | print `Hello, TraceFix!` | retry once, then stop when behavior still lacks a safe bounded patch | failure summary plus verifier mismatch evidence |
| `bug_case_07_failure_ambiguous_behavior` | `bug_case_07_failure_ambiguous_behavior.py` | failure: ambiguous behavior | output intent is not supplied to the verifier | escalate because the crash is removed but behavior cannot be trusted automatically | escalated session with no behavior oracle |

## Recommended Demo Cases

- Best happy-path demo: `bug_case_02_name_error.py`
- Best retry-path demo: `bug_case_06_failure_superficial_fix.py`
- Best conservative-stop demo: `bug_case_05_runtime_exception.py`

## Best Failure Analysis Cases

- `bug_case_06_failure_superficial_fix.py`
  - Shows why removing the original crash is not enough.
- `bug_case_07_failure_ambiguous_behavior.py`
  - Shows why the verifier remains conservative without an explicit behavior oracle.
