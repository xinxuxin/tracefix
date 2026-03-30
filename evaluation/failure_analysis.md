# Failure Analysis

This document summarizes the most important failure modes for the current TraceFix prototype and aligns them with the implemented controller and verifier behavior.

## Current Failure Modes

### 1. Unsupported Runtime Failures

Representative case:

- `bug_case_05_runtime_exception`

Why it happens:

- the executor captures a real runtime exception
- the diagnoser can localize the failure, but the patcher does not have a safe bounded transformation for that bug class
- the controller therefore stops instead of widening scope

Evidence to capture:

- `trace.jsonl`
- `session_state.json`
- `failure_summary.md`
- verifier or patch refusal rationale

### 2. Superficial Fix That Removes the Crash but Not the Behavior Problem

Representative case:

- `bug_case_06_failure_superficial_fix`

Why it happens:

- the patcher makes a plausible localized change
- the rerun no longer shows the original exception
- expected output still does not match, so the verifier refuses acceptance

Why it matters:

- this is the clearest example of why TraceFix uses a separate verifier instead of accepting “no crash” as success

Evidence to capture:

- original execution result
- rerun execution result
- verifier decision and behavior mismatch status
- final failure summary

### 3. Ambiguous Successful Rerun Without a Strong Oracle

Representative case:

- `bug_case_07_failure_ambiguous_behavior`

Why it happens:

- a bounded patch removes the observed crash
- no expected output or stronger behavioral check is available
- the verifier escalates because successful execution alone is not trustworthy enough

Why it matters:

- this is the best governance example in the repository
- it shows that the system is conservative under uncertainty

Evidence to capture:

- rerun stdout
- verifier rationale
- `behavior_match_status`
- final escalation decision

### 4. Over-Conservative Refusal

Why it happens:

- TraceFix intentionally prioritizes low-risk behavior
- some cases that a human could probably fix are still refused or escalated because the system lacks enough evidence

Why it matters:

- it lowers apparent automation coverage
- but it strengthens credibility and governance for a course project

Evidence to capture:

- diagnoser uncertainty notes
- patch refusal reason
- verifier targeted feedback

## What the Current System Already Does Well

- It distinguishes direct crash removal from true acceptance.
- It preserves explicit stopping and escalation behavior.
- It leaves an inspectable evidence trail for each unresolved case.

## Reasonable Future Improvements

- add a small number of additional safe patch strategies for common runtime failures
- improve diagnosis for behavior-level mismatches when expected output is available
- support richer but still bounded test oracles
- improve artifact summaries so failure analysis can be written faster from saved session files
