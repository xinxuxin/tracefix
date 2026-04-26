# Phase 3 Submission Checklist

Validation date: 2026-04-26

| Requirement | Status | Owner | Evidence path | Remaining action |
|---|---|---|---|---|
| Working source code | complete | Xin Xu | `src/tracefix/`, `frontend/src/` | None. CLI, tests, visual API, and frontend build were validated. |
| Runnable repository instructions | complete | Xin Xu | `README.md`, `docs/run_instructions.md` | None. |
| Final artifact | complete | Xin Xu | Repository source and generated evaluation artifacts | None for code artifact. |
| Final presentation/demo plan | complete | Fan Yang | `docs/frontend_demo_notes.md`, `docs/demo_script_notes.md`, `docs/project_video_speech_notes.md`, `docs/project_video_storyboard.md` | Use the main page during recording. |
| 5-minute video artifact | complete | Fan Yang | `media/tracefix_phase3_demo.mp4`, `media/demo_video_link.txt` | None if Canvas accepts uploaded MP4. If Canvas requires a hosted URL, upload this MP4 and paste the URL in `media/demo_video_link.txt`. |
| Final report draft | partial | Siru Tao | `docs/final_report_draft.md` | Review, polish, and export to required final format if Canvas expects PDF. |
| Evidence package | complete | Xin Xu | `evaluation/runs/20260425T180442Z` | None. Latest run is included and root CSVs point to it. |
| At least 5 completed test scenarios | complete | Xin Xu | `evaluation/evaluation_results.csv` | None. 7 executed cases verified. |
| Results for each case | complete | Xin Xu | `evaluation/evaluation_results.csv` | None. Includes actual behavior, decisions, metrics, and artifact paths. |
| At least 2 failure cases | complete | Crystal Huang | `evaluation/failure_log.md`, `docs/phase3_failure_analysis.md` | None. 3 failure/boundary cases documented. |
| What changed after testing | complete | Crystal Huang | `evaluation/failure_log.md`, `docs/phase3_failure_analysis.md` | None. |
| Supporting traces/logs/outputs | complete | Xin Xu | `evaluation/runs/20260425T180442Z/cases/` | None. Each evaluated case has `trace.jsonl`, `session_state.json`, and `summary.md`. |
| Architecture/design choices | complete | Siru Tao | `docs/architecture_overview.md` | None. |
| Model/provider assignments | complete | Xin Xu | `docs/model_and_provider_policy.md`, `src/tracefix/config.py` | None. Includes model names, temperature, max tokens, fallback, and logging policy. |
| Formal state schema | complete | Xin Xu | `docs/state_schema.md`, `src/tracefix/models.py`, `src/tracefix/state.py`, `src/tracefix/types.py` | None. |
| Governance and safety reflection | complete | Crystal Huang | `docs/governance_and_risks.md`, `docs/executor_notes.md` | None. |
| Sandbox tests | complete | Xin Xu | `tests/test_executor.py` | None. Timeout, blocked policy, missing file, shell/eval/path blocks validated. |
| Project Video / Demo Evidence: main page video roadmap | complete | Xin Xu | `frontend/src/App.tsx`, `/#demo-roadmap` | None. |
| Project Video / Demo Evidence: speech notes | complete | Fan Yang | `docs/project_video_speech_notes.md` | Presenter should rehearse and adapt naturally. |
| Project Video / Demo Evidence: storyboard | complete | Fan Yang | `docs/project_video_storyboard.md` | None. |
| Project Video / Demo Evidence: click path | complete | Fan Yang | `docs/demo_click_path.md` | None. |
| Project Video / Demo Evidence: recording checklist | complete | Fan Yang | `docs/video_recording_checklist.md` | Use immediately before recording. |
| Project Video / Demo Evidence: requirement coverage | complete | Xin Xu | `docs/demo_requirement_coverage.md` | None. |
| Project Video / Demo Evidence: happy-path case | complete | Xin Xu | `cases/bug_case_02_name_error.py`, `/#workspace` | None. |
| Project Video / Demo Evidence: failure/boundary cases | complete | Crystal Huang | `cases/bug_case_06_failure_superficial_fix.py`, `cases/bug_case_07_failure_ambiguous_behavior.py`, `/#evaluation` | None. |
| Project Video / Demo Evidence: evaluation dashboard | complete | Xin Xu | `evaluation/evaluation_results.csv`, `/#evaluation` | None. |
| Project Video / Demo Evidence: session artifacts | complete | Xin Xu | `outputs/sessions/`, `evaluation/runs/20260425T180442Z/`, `/#explorer`, `/#final-output` | None. |
| Frontend evidence docs | partial | Fan Yang | `docs/frontend_demo_notes.md`, `docs/screenshots/screenshot_index.md` | Capture final 4 to 8 named report screenshots from the main page. |
| Frontend build | complete | Xin Xu | `frontend/dist/`, `docs/phase3_validation_report.md` | None. `npm run build` passed. |
| Visual API / local demo adapter | complete | Xin Xu | `src/tracefix/visual_api.py`, `tests/test_visual_api.py` | None. `/api/health`, `/api/evaluation`, and static index serving were validated locally. |
| Baseline comparison | complete | Xin Xu | `evaluation/baseline_comparison.csv`, `docs/baseline_comparison.md` | None. Deterministic crash-only baseline documented. |
| AI usage disclosure | partial | Xin Xu | `AI_USAGE.md`, `docs/ai_prompt_appendix.md`, `docs/ai_logs/` | Attach exported full AI response logs. Current `docs/ai_logs/` contains only README instructions. |
| Phase 3 owners and estimates | partial | Xin Xu | `docs/phase3_workplan.md` | Team should confirm due dates and suggested ownership. |
| Individual reflections | MANUAL_REQUIRED | All team members | `docs/phase3_workplan.md` | Add or attach each teammate's individual reflection before submission. |
| Screenshots | partial | Fan Yang | `docs/screenshots/screenshot_index.md`, `docs/screenshots/tracefix_after_run_full_page_desktop_20260425.png` | Full-page screenshots exist; final named 4-8 screenshot set still needs capture. |
| Validation report | complete | Xin Xu | `docs/phase3_validation_report.md` | None after this audit. |

## Overall Status

The repository is technically runnable and the evidence package is complete. A 5-minute demo MP4 is now included in `media/`. Final submission is **not fully ready** until the remaining human-owned submission artifacts are added: final named report screenshots, exported full AI response logs, final report export, and individual reflections.
