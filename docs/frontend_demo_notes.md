# Frontend Demo Notes

## Purpose

The frontend is an optional local visualization layer for TraceFix. It exists to make the current repository easier to demo, easier to screenshot, and easier to explain in a course report. It is not a replacement for the CLI and it does not change the core debugging scope.

## What the Frontend Shows

- project overview and scope reminder
- debug workspace for pasted code or sample cases
- animated pipeline view for Controller, Executor, Diagnoser, Patcher, and Verifier
- trace timeline from `trace.jsonl`
- patch diff and changed-region view
- final verifier decision panel
- sample case library
- evaluation dashboard from existing CSV outputs
- failure analysis highlights
- session artifact paths and summaries

## Recommended 5-Minute Demo Flow

1. Start on the hero section and explain the target user and why TraceFix is agentic.
2. Load `bug_case_02_name_error` as the quick happy-path example.
3. Run TraceFix and pause on:
   - the pipeline view
   - the verifier result panel
   - the patch diff
4. Scroll to the trace timeline and show the explicit handoff events.
5. Jump to the evaluation dashboard and show the full case set.
6. End on the failure analysis cards for:
   - `bug_case_06_failure_superficial_fix`
   - `bug_case_07_failure_ambiguous_behavior`

## Best Screenshot Sequence

1. Hero + architecture summary
2. Debug workspace with a sample case loaded
3. Pipeline view after a run
4. Trace timeline with expanded handoff details
5. Patch diff and verifier result together
6. Evaluation dashboard
7. Failure analysis section
8. Session artifacts section showing saved paths

## Best Cases for the Frontend

Best quick success demo:

- `bug_case_02_name_error`
- `bug_case_04_missing_file`

Best governance demos:

- `bug_case_06_failure_superficial_fix`
- `bug_case_07_failure_ambiguous_behavior`

Best conservative stop:

- `bug_case_05_runtime_exception`

## Architecture Mapping

The frontend does not duplicate controller logic. Instead:

- `TraceFixController` still runs the end-to-end workflow
- `TraceFixVisualService` is only a thin adapter
- the frontend reads:
  - sample cases from `cases/`
  - sessions from `outputs/sessions/`
  - evaluation results from `evaluation/runs/`

That keeps the project course-appropriate while making the system much easier to inspect visually.
