# Phase 3 Submission Checklist

| Requirement | Status | Evidence path | Notes |
|---|---|---|---|
| Working source code | complete | `src/tracefix/`, `frontend/src/` | CLI and frontend build validated. |
| Runnable repository instructions | complete | `README.md`, `docs/run_instructions.md` | Includes CLI, evaluation, provider, and frontend commands. |
| Final artifact | complete | repository source and generated evaluation artifacts | TraceFix remains local-first and runnable. |
| Final presentation/demo plan | partial | `docs/frontend_demo_notes.md`, `media/demo_video_link.txt` | Video link still `TODO_FOR_TEAM`. |
| 5-minute video or placeholder | TODO_FOR_TEAM | `media/demo_video_link.txt` | Add actual link before submission. |
| Final report draft | partial | `docs/final_report_draft.md` | Ready for team review/export; not yet PDF. |
| Evidence package | complete | `evaluation/runs/20260425T172418Z` | Includes 7 case runs and per-case artifacts. |
| At least 5 completed test scenarios | complete | `evaluation/evaluation_results.csv` | 7 executed cases. |
| Results for each case | complete | `evaluation/evaluation_results.csv` | Includes actual behavior, decisions, metrics, and artifact paths. |
| At least 2 failure cases | complete | `evaluation/failure_log.md`, `docs/phase3_failure_analysis.md` | Includes unsupported runtime, superficial fix, and no-oracle escalation. |
| What changed after testing | complete | `evaluation/failure_log.md`, `docs/phase3_failure_analysis.md` | Documents retained cases and runner adjustment. |
| Supporting traces/logs/outputs | complete | `evaluation/runs/20260425T172418Z/cases/` | Each case includes `trace.jsonl`, `session_state.json`, and `summary.md`. |
| Architecture/design choices | complete | `docs/architecture_overview.md` | Includes handoffs, tools, state, model assignments. |
| Model/provider assignments | complete | `docs/model_and_provider_policy.md` | Includes default models, temperature, max tokens, fallback, logging. |
| Formal state schema | complete | `docs/state_schema.md` | Includes fields, types, writers, readers, persistence. |
| Governance and safety reflection | complete | `docs/governance_and_risks.md` | Includes lightweight sandbox specificity and limitations. |
| Sandbox tests | complete | `tests/test_executor.py` | Timeout, blocked policy, missing file, shell/eval/path blocks. |
| Frontend evidence docs | partial | `docs/frontend_demo_notes.md`, `docs/screenshots/screenshot_index.md` | Screenshot images still need capture. |
| Baseline comparison | complete | `evaluation/baseline_comparison.csv`, `docs/baseline_comparison.md` | Deterministic crash-only baseline. |
| AI usage disclosure | partial | `AI_USAGE.md`, `docs/ai_prompt_appendix.md`, `docs/ai_logs/` | Disclosure and appendix exist. Remaining action: attach exported full AI response logs because they were not found in the repository. |
| Phase 3 owners and estimates | partial | `docs/phase3_workplan.md` | Suggested owners included; team must confirm due dates. |
| Individual reflections | TODO_FOR_TEAM | `docs/phase3_workplan.md` | Add each teammate reflection before final submission. |
| Validation report | complete | `docs/phase3_validation_report.md` | Records evaluation, tests, and frontend build outcomes. |

## Overall Status

Phase 3 repository readiness is **partial but close**. Code, evaluation, architecture, governance, state schema, baseline comparison, and validation are complete. Remaining items are team-owned submission artifacts: screenshots, final video link, exact AI usage confirmations, final report export, and individual reflections.
