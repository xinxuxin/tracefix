# Frontend Demo Notes

## Purpose

The frontend is still an optional local visualization layer for TraceFix. It does not replace the CLI and it does not widen the debugging scope. Its purpose is to make the existing system easier to explain, easier to inspect, and easier to capture in screenshots or a short demo video.

## What Changed in the Frontend Upgrade

The upgraded frontend keeps the same data flow and the same feature set, but improves:

- visual clarity and technical credibility
- information hierarchy
- demo sequencing
- session storytelling
- trace and diff readability
- retry and artifact inspection
- screenshot quality

The style direction is now cooler, sharper, and more dashboard-like rather than painterly or decorative.

## Best 5-Minute Demo Sequence

1. Start on the top bar and hero section.
   Explain that this is a visual layer on top of the existing bounded CLI workflow.
2. Point to the hero system strip.
   Use it to name the five core components: Controller, Executor, Diagnoser, Patcher, Verifier.
3. Move to the Debug Workspace.
   Load `bug_case_02_name_error` or `bug_case_04_missing_file`.
4. Run TraceFix.
   While it runs, keep the Pipeline View visible so the handoff progression is obvious.
5. Pause on the Final Decision panel.
   Explain why verifier authority matters.
6. Open the Session Explorer.
   Show:
   - `Trace timeline` for handoffs
   - `Patch diff` for the bounded edit
   - `Artifacts` for saved report evidence
7. Jump to the Evaluation Dashboard.
   Show the summary cards and table.
8. End on Failure Analysis.
   Use `bug_case_06_failure_superficial_fix` and `bug_case_07_failure_ambiguous_behavior`.

## Best Screenshot Sections

Track screenshot capture status in [docs/screenshots/screenshot_index.md](docs/screenshots/screenshot_index.md).

Best architecture / system screenshots:

- sticky top bar plus dark hero section
- hero system strip
- pipeline view with component status cards

Best workflow / evidence screenshots:

- debug workspace with a sample loaded
- final decision panel
- trace timeline with payload expanded
- patch diff tab
- artifacts tab with summary preview

Best evaluation / report screenshots:

- evaluation summary cards
- evaluation results table
- failure analysis cards

## Best Interactions To Show

- loading a sample case from the sample browser
- running TraceFix from the workspace
- switching Session Explorer tabs
- filtering the trace timeline by component
- switching between split code view and unified diff view
- selecting an intermediate patch attempt
- switching artifact preview modes

These interactions make the frontend feel alive without changing backend behavior.

## Best Cases To Use

Best quick success demo:

- `bug_case_02_name_error`
- `bug_case_04_missing_file`

Best governance / limitation demos:

- `bug_case_06_failure_superficial_fix`
- `bug_case_07_failure_ambiguous_behavior`

Best conservative stop:

- `bug_case_05_runtime_exception`

## Which Sections Explain What

Architecture explanation:

- hero section
- top system strip
- pipeline view

Evidence explanation:

- trace timeline
- patch diff
- artifacts preview

Verifier and governance explanation:

- final decision panel
- failure analysis cards

Evaluation explanation:

- evaluation dashboard
- outcome distribution
- results table

## Presentation Notes

- Keep the app on a common laptop-sized viewport when recording.
- Prefer one successful run and one failure-analysis jump instead of trying to show every panel in depth.
- The new Session Explorer is the main detail surface, so it is a strong place to pause for screenshots.
- The dark hero plus light detail panels produce the cleanest visual contrast in screenshots.
