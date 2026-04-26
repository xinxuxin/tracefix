# Screenshot Index

Final screenshots should be captured before Phase 3 submission. Some full-page screenshots are already present, but the final report should still capture the named 4-8 screenshots below from the main page.

Existing full-page captures:

- `tracefix_after_run_full_page_desktop_20260425.png`
- `tracefix_presentation_mode_full_page_20260426.png`
- `tracefix_full_page_desktop_20260425.png`
- `tracefix_full_page_20260425.png`

| Screenshot | Status | Purpose | Suggested source |
|---|---|---|---|
| `01_home_or_overview.png` | MANUAL_REQUIRED | Show TraceFix identity, scope, system map, and video roadmap | `/` hero and `#demo-roadmap` |
| `02_debug_workspace.png` | MANUAL_REQUIRED | Show happy-path code and run action | `/#workspace` |
| `03_pipeline_handoff.png` | MANUAL_REQUIRED | Show Controller/Executor/Diagnoser/Patcher/Verifier handoff flow | `/#session-story` |
| `04_trace_timeline.png` | MANUAL_REQUIRED | Show inspectable trace events and payload detail | `/#explorer` trace tab |
| `05_patch_diff.png` | MANUAL_REQUIRED | Show original vs patched code or unified diff | `/#explorer` diff tab |
| `06_verification_result.png` | MANUAL_REQUIRED | Show accept/stop/escalate rationale and behavior indicators | `/#session-story` |
| `07_evaluation_dashboard.png` | MANUAL_REQUIRED | Show 7-case evaluation summary and results table | `/#evaluation` |
| `08_failure_case.png` | MANUAL_REQUIRED | Show failure/governance story cards | `/#evaluation` failure cards |

## Capture Instructions

1. Start the local visual server: `PYTHONPATH=src python -m tracefix visual-server --port 8123`.
2. Open `http://127.0.0.1:8123/`.
3. Click `Run TraceFix` for `bug_case_02_name_error`.
4. Capture 4 to 8 screenshots using the filenames above.
5. Keep captions below aligned with the final report or slide deck.

## Captions

Use these captions in the report or slide deck:

- `01_home_or_overview.png`: TraceFix local visual demo layer showing the bounded multi-component architecture.
- `02_debug_workspace.png`: Sample-case workspace with optional expected output used as a verifier oracle.
- `03_pipeline_handoff.png`: Agent handoff visualization for Controller, Executor, Diagnoser, Patcher, and Verifier.
- `04_trace_timeline.png`: JSONL trace events surfaced as inspectable evidence artifacts.
- `05_patch_diff.png`: Minimal patch diff generated during a TraceFix run.
- `06_verification_result.png`: Verifier decision panel showing why a patch was accepted, stopped, or escalated.
- `07_evaluation_dashboard.png`: Phase 3 evaluation results across seven cases.
- `08_failure_case.png`: Failure-analysis view showing conservative stopping and no-oracle escalation.
