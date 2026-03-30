# Failure Analysis Seed Notes

## Likely Failure Cases

### Superficial Fix

Example:

- `bug_case_06_failure_superficial_fix`

Why it happens:

- the patch removes the original crash
- the remaining behavior still does not match the intended output
- the diagnoser may not have enough evidence for a safe second patch

Evidence to capture:

- original trace
- rerun trace
- verifier mismatch decision
- session summary
- failure summary

Possible future improvement:

- stronger logic-level diagnosis when explicit expected output exists

### Ambiguous Behavior

Example:

- `bug_case_07_failure_ambiguous_behavior`

Why it happens:

- a local fix can remove the crash
- no expected output or test oracle is available
- verifier should escalate instead of accepting blindly

Evidence to capture:

- successful rerun output
- verifier rationale showing no behavior oracle
- final escalation decision

Possible future improvement:

- lightweight user-facing clarification prompts for expected behavior

### Unsupported Runtime Exceptions

Example:

- `bug_case_05_runtime_exception`

Why it happens:

- the runtime failure is real but outside the current bounded patch strategies
- a safe local patch cannot be justified

Evidence to capture:

- executor evidence
- diagnoser confidence and uncertainty
- patch refusal
- final stop decision

Possible future improvement:

- extend patcher support for additional safe runtime categories

### Over-Conservative Escalation

Why it happens:

- verifier intentionally avoids false-positive acceptance
- this can leave some likely-correct patches unresolved

Evidence to capture:

- patch breadth
- behavior match status
- final escalation rationale

Possible future improvement:

- richer behavioral checks or tiny test oracles supplied by the user

## Report Guidance

For the final report, the strongest failure-analysis section will compare:

- what failed originally
- what the system changed
- what the rerun showed
- why the final decision was still not acceptance
- what narrowly scoped future improvement could help
