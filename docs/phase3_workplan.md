# Phase 3 Workplan

This is a suggested owner plan for final submission. Assignments marked `TODO_FOR_TEAM_CONFIRM` should be confirmed by the team before submission.

| Deliverable | Suggested owner | Estimate | Due date | Status | Notes |
|---|---|---:|---|---|---|
| 5-minute project video | Fan Yang | 3-4 hours | TODO_FOR_TEAM_CONFIRM | TODO_FOR_TEAM | Use frontend demo flow in `docs/frontend_demo_notes.md`. |
| Final report | Siru Tao | 4-6 hours | TODO_FOR_TEAM_CONFIRM | TODO_FOR_TEAM | Start from `docs/final_report_draft.md`. |
| Evidence package assembly | Xin Xu | 2-3 hours | TODO_FOR_TEAM_CONFIRM | partial | Evaluation artifacts and docs are generated; screenshots/video still need capture. |
| Evaluation execution and results | Xin Xu | 1-2 hours | 2026-04-25 | complete | Latest run: `evaluation/runs/20260425T172418Z`. |
| Failure analysis write-ups | Crystal Huang | 2-3 hours | TODO_FOR_TEAM_CONFIRM | partial | Drafts exist in `evaluation/failure_log.md` and `docs/phase3_failure_analysis.md`. |
| AI usage disclosure | Siru Tao | 1-2 hours | TODO_FOR_TEAM_CONFIRM | partial | `AI_USAGE.md` exists; team-specific tool/version details need confirmation. |
| Screenshots and frontend demo evidence | Fan Yang | 2-3 hours | TODO_FOR_TEAM_CONFIRM | TODO_FOR_TEAM | Capture 4-8 screenshots listed in `docs/screenshots/screenshot_index.md`. |
| Final repository cleanup | Xin Xu | 1 hour | TODO_FOR_TEAM_CONFIRM | partial | Remove/ignore local generated folders if needed; verify clean git state before submission. |
| Individual reflection: Fan Yang | Fan Yang | 30-45 minutes | TODO_FOR_TEAM_CONFIRM | TODO_FOR_TEAM | Include concrete contributions and lessons learned. |
| Individual reflection: Siru Tao | Siru Tao | 30-45 minutes | TODO_FOR_TEAM_CONFIRM | TODO_FOR_TEAM | Include documentation/report contributions. |
| Individual reflection: Crystal Huang | Crystal Huang | 30-45 minutes | TODO_FOR_TEAM_CONFIRM | TODO_FOR_TEAM | Include failure-analysis/evaluation review. |
| Individual reflection: Xin Xu | Xin Xu | 30-45 minutes | TODO_FOR_TEAM_CONFIRM | TODO_FOR_TEAM | Include implementation/evidence package work. |

## Suggested Final Sequence

1. Confirm team ownership and due dates.
2. Capture screenshots and video.
3. Review `AI_USAGE.md` and add missing teammate-specific tool usage.
4. Convert or export `docs/final_report_draft.md` into the final report format.
5. Re-run validation commands before submission.
6. Commit final evidence package and submit repository/video/report links.

## Submission Risks

| Risk | Mitigation |
|---|---|
| AI usage details are incomplete | Keep `TODO_FOR_TEAM` markers visible until teammates confirm. |
| Screenshots are missing | Use `docs/screenshots/screenshot_index.md` as a capture checklist. |
| Video link is missing | Fill `media/demo_video_link.txt` before final submission. |
| Evaluation results become stale after code changes | Re-run `PYTHONPATH=src python3 evaluation/run_evaluation.py`. |
