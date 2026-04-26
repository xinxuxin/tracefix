# Demo Script Notes

This outline is for the required 5-minute Phase 3 project video. It is a recording guide only; the actual video link must be added to `media/demo_video_link.txt` before final submission.

## 5-Minute Video Outline

| Time | Segment | What to show | Evidence path |
|---|---|---|---|
| 0:00-0:30 | Problem and target user | Explain the beginner-to-intermediate single-file Python debugging problem and the concrete `NameError` motivating scenario. | `README.md`, `docs/final_report_draft.md` |
| 0:30-1:10 | Architecture | Show Controller, Executor, Diagnoser, Patcher, and Verifier. Emphasize bounded retries, local artifacts, and conservative verification. | `docs/architecture_overview.md`, frontend hero/system map |
| 1:10-2:30 | Main workflow | Load `bug_case_02_name_error.py`, run TraceFix, and show accept decision with expected output `10.70`. | `cases/bug_case_02_name_error.py`, `outputs/sessions/`, frontend workspace |
| 2:30-3:20 | Evidence layer | Open trace timeline, patch diff, verification result, and session artifacts. Explain that `trace.jsonl`, `session_state.json`, and `summary.md` are saved locally. | `evaluation/runs/20260425T180442Z/cases/` |
| 3:20-4:20 | Failure/boundary case | Show `bug_case_06_failure_superficial_fix.py` or `bug_case_07_failure_ambiguous_behavior.py`. Explain why TraceFix stops or escalates instead of accepting "no crash" as success. | `evaluation/failure_log.md`, `docs/phase3_failure_analysis.md` |
| 4:20-5:00 | Evaluation and limitations | Show the 7-case evaluation dashboard, baseline comparison, lightweight sandbox limitation, and remaining future work. | `evaluation/evaluation_results.csv`, `docs/baseline_comparison.md`, `docs/governance_and_risks.md` |

## Recording Checklist

- Start the visual server with `PYTHONPATH=src python -m tracefix visual-server --port 8123`.
- Start the frontend dev server from `frontend/` with `npm run dev`, or use the built frontend served by the visual server.
- Capture one happy-path run and one failure/boundary case.
- Mention that the Phase 3 evidence was produced in deterministic local mode.
- Do not claim that screenshots, video, or full AI response logs are complete unless those artifacts are present in the repository.
