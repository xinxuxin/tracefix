# Phase 3 Workplan

This is a suggested owner plan for final submission. Owner names are proposed for coordination and should be confirmed by the team during final packaging.

| Deliverable | Suggested owner | Estimate | Due date | Status | Notes |
|---|---|---:|---|---|---|
| 5-minute project video | Fan Yang | 3-4 hours | Before final submission | complete | Demo MP4 is included at `media/tracefix_phase3_demo.mp4`; use `media/demo_video_link.txt` if a hosted URL is required. |
| Final report | Siru Tao | 4-6 hours | Before final submission | partial | Draft exists in `docs/final_report_draft.md`; export to the required final format before submission. |
| Evidence package assembly | Xin Xu | 2-3 hours | Before final submission | partial | Evaluation artifacts, docs, and demo video are present; final named screenshots still need capture. |
| Evaluation execution and results | Xin Xu | 1-2 hours | 2026-04-25 | complete | Latest run: `evaluation/runs/20260425T180442Z`. |
| Failure analysis write-ups | Crystal Huang | 2-3 hours | Before final submission | complete | Write-ups exist in `evaluation/failure_log.md` and `docs/phase3_failure_analysis.md`. |
| AI usage disclosure | Siru Tao | 1-2 hours | Before final submission | partial | `AI_USAGE.md` exists; exported full AI conversation logs still require team attachment if the course requests them. |
| Screenshots and frontend demo evidence | Fan Yang | 2-3 hours | Before final submission | partial | Full-page captures exist; final named screenshots listed in `docs/screenshots/screenshot_index.md` should be captured for the report. |
| Final repository cleanup | Xin Xu | 1 hour | Before final submission | partial | Validate git status after final edits and confirm pushed commit. |
| Individual reflection: Fan Yang | Fan Yang | 30-45 minutes | Before final submission | manual_required | Include concrete contributions and lessons learned in the final report/submission form. |
| Individual reflection: Siru Tao | Siru Tao | 30-45 minutes | Before final submission | manual_required | Include documentation/report contributions. |
| Individual reflection: Crystal Huang | Crystal Huang | 30-45 minutes | Before final submission | manual_required | Include failure-analysis/evaluation review. |
| Individual reflection: Xin Xu | Xin Xu | 30-45 minutes | Before final submission | manual_required | Include implementation/evidence package work. |

## Suggested Final Sequence

1. Confirm team ownership and due dates.
2. Capture final named screenshots.
3. Review `AI_USAGE.md` and add missing teammate-specific tool usage.
4. Convert or export `docs/final_report_draft.md` into the final report format.
5. Re-run validation commands before submission.
6. Commit final evidence package and submit repository/video/report links.

## Submission Risks

| Risk | Mitigation |
|---|---|
| Full AI response exports are missing | Attach exported conversations under `docs/ai_logs/` if the course grader requires the full responses. |
| Final named screenshots are not all present | Use `docs/screenshots/screenshot_index.md` as a capture checklist. |
| Hosted video URL may be required | `media/tracefix_phase3_demo.mp4` is included; if Canvas requires a hosted link, paste it in `media/demo_video_link.txt`. |
| Evaluation results become stale after code changes | Re-run `PYTHONPATH=src python3 evaluation/run_evaluation.py`. |
