# TraceFix Evaluation Plan

## Why These Cases Were Chosen

The evaluation set is designed to reflect the narrow but realistic scope of TraceFix:

- syntax repair
- name error repair
- argument mismatch repair
- missing resource repair
- unsupported runtime failure with conservative stopping
- behavioral false-positive risk
- ambiguous behavior with insufficient verification evidence

Together, these cases show both useful automation and deliberate refusal.

## What Counts as Success

A case counts as successful when the system outcome matches the intended governance decision for that case:

- `accept` for bounded, evidence-supported fixes
- `stop` for unsupported or unsafe-to-patch cases
- `escalate` when execution succeeds but verification evidence is too weak

For repairable cases, success also requires:

- original failure resolved
- behavior match status aligned with expected output when provided
- a saved patch artifact and trace

## What Counts as Failure

A run counts as failure when:

- the system accepts a patch without enough behavioral evidence
- the system retries endlessly instead of stopping or escalating
- the patch is overly broad relative to the diagnosis
- a repairable case is left unresolved without a strong reason

## Metrics Used

The evaluation runner records these fields where feasible:

- task success
- final decision / outcome label
- retry count
- total latency in milliseconds
- patch breadth or diff size
- whether the original failure was resolved
- whether behavior matched expectation

## Reproducible Artifacts

Each evaluation run writes a timestamped folder under `evaluation/runs/` containing:

- `evaluation_results.csv`
- `failure_cases.csv`
- `run_summary.md`
- per-case session folders with traces and patch artifacts

Each session folder contains the controller outputs:

- `trace.jsonl`
- `session_state.json`
- `summary.md`
- `failure_summary.md` when unresolved
- intermediate patch candidates and diffs
- final patched script when accepted

## Course Evidence Package Notes

- Logs live under `evaluation/runs/<timestamp>/cases/<case_id>/...`
- Screenshots can be taken from the CLI summary plus the per-session `summary.md` and `trace.jsonl`
- Best cases for a demo video:
  - `bug_case_02_name_error`
  - `bug_case_04_missing_file`
  - `bug_case_06_failure_superficial_fix`
- Best cases for failure analysis:
  - `bug_case_06_failure_superficial_fix`
  - `bug_case_07_failure_ambiguous_behavior`

## Limitations

- The evaluation suite remains single-file only.
- Behavioral checking is strongest when explicit expected output is supplied.
- TraceFix still does not solve broad semantic program repair or multi-file debugging.
