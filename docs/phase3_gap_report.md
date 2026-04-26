# Phase 3 Gap Report

This report maps Phase 1 and Phase 2 feedback to repository fixes for Phase 3.

| Feedback item | Current repo status before fix | Fix needed | Files updated / created | Status after fix | Evidence path |
|---|---|---|---|---|---|
| AI usage disclosure missing | Template existed, root-level completed disclosure was absent | Add completed `AI_USAGE.md` and prompt appendix | `AI_USAGE.md`, `docs/ai_prompt_appendix.md` | partial | Full exported AI response logs still require team attachment if required by the course |
| Evaluation results CSV blank | `evaluation/results_template.csv` existed but was not final evidence | Run all cases and generate populated CSVs | `evaluation/run_evaluation.py`, `evaluation/evaluation_results.csv`, `evaluation/test_cases.csv`, `evaluation/summary.md` | complete | `evaluation/runs/20260425T180442Z` |
| At least two failure cases executed/analyzed | Failure-analysis seed existed, but executed final logs were incomplete | Run and document failure/governance cases | `evaluation/failure_log.md`, `docs/phase3_failure_analysis.md` | complete | `bug_case_06_failure_superficial_fix`, `bug_case_07_failure_ambiguous_behavior` |
| LLM model assignments missing centrally | Provider code existed; central docs lacked full assignment table | Add model/provider policy and architecture section | `docs/model_and_provider_policy.md`, `docs/architecture_overview.md`, `README.md` | complete | config defaults and provider docs |
| State schema not formalized | `state.py` and `types.py` existed; write permissions were prose-only | Add schema table and write permissions | `docs/state_schema.md`, `docs/architecture_overview.md` | complete | `src/tracefix/state.py`, `src/tracefix/types.py` |
| Sandbox enforcement lacked specificity | Executor docs mentioned safety but did not cite all mechanisms | Document exact mechanisms and add minimal policy/test coverage | `docs/governance_and_risks.md`, `docs/executor_notes.md`, `src/tracefix/sandbox/policy.py`, `tests/test_executor.py` | complete | validation report and tests |
| Frontend not evidenced | Frontend existed and demo notes existed; screenshot inventory was placeholder-only | Add screenshot index and demo video evidence | `docs/frontend_demo_notes.md`, `docs/screenshots/screenshot_index.md`, `docs/screenshots/README.md`, `media/demo_video_link.txt`, `media/tracefix_phase3_demo.mp4` | partial | demo video is included; final named screenshots should still be captured for the report |
| Baseline comparison conceptual | No executed baseline comparison CSV | Add deterministic crash-only baseline | `evaluation/baseline_comparison.csv`, `docs/baseline_comparison.md`, `evaluation/run_evaluation.py` | complete | `evaluation/baseline_comparison.csv` |
| Phase 3 owners not assigned | No owner workplan | Add suggested owner plan with estimates | `docs/phase3_workplan.md` | partial | ownership and due dates need team confirmation |
| Problem statement needs concrete scenario | README had target user but not a specific failure story | Add NameError motivating scenario | `README.md`, `docs/project_summary.md`, `docs/final_report_draft.md` | complete | problem sections in docs |

## Remaining Manual Actions

- Attach exported full AI response logs under `docs/ai_logs/` if required by the course.
- Capture and add the final named 4-8 screenshots listed in `docs/screenshots/screenshot_index.md`.
- If Canvas requires a hosted video URL instead of a repository MP4, upload `media/tracefix_phase3_demo.mp4` and paste the URL in `media/demo_video_link.txt`.
- Confirm owner assignments and due dates during team handoff.
- Complete individual contribution reflections.
- Convert or export `docs/final_report_draft.md` into the required final report format.
