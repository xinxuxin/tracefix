# Baseline Comparison

Phase 2 feedback noted that the baseline comparison was conceptual. The Phase 3 package now includes a deterministic baseline evaluated against the same cases as TraceFix.

## Baseline Definition

Baseline name: `deterministic_crash_only_acceptance`

The baseline accepts any patched rerun that exits without crashing. It does not use:

- expected-output matching
- no-oracle escalation
- independent verifier rationale
- regression flags
- conservative stopping based on behavioral uncertainty

This is intentionally simple and fair for a local-only repository because it does not require API keys or fake provider calls.

## Evidence

- [evaluation/baseline_comparison.csv](evaluation/baseline_comparison.csv)
- [evaluation/evaluation_results.csv](evaluation/evaluation_results.csv)
- [evaluation/runs/20260425T180442Z/baseline_comparison.csv](evaluation/runs/20260425T180442Z/baseline_comparison.csv)

## Results Summary

| Case group | Baseline behavior | TraceFix behavior |
|---|---|---|
| Repairable syntax/name/argument/missing-file cases | Accepts because rerun succeeds | Accepts because rerun succeeds and expected output matches |
| Unsupported runtime exception | Stops because no non-crashing rerun exists | Stops because patcher lacks a safe bounded strategy |
| Superficial fix case | Accepts the non-crashing rerun | Stops because output is `HELLO, TRACEFIX!` instead of `Hello, TraceFix!` |
| Ambiguous no-oracle case | Accepts the non-crashing rerun | Escalates because successful execution alone is insufficient |

## Interpretation

The baseline shows why TraceFix needs a Verifier. For two governance cases, crash-only acceptance would overstate success:

- `bug_case_06_failure_superficial_fix`
- `bug_case_07_failure_ambiguous_behavior`

TraceFix makes a stricter decision because it checks expected behavior when available and escalates when no behavior oracle exists.

## Limitation

This baseline is deterministic and local. It does not represent a full one-shot LLM baseline because no API key was assumed for final evaluation. That limitation is intentional and reproducible: the repository can be graded without external services.
