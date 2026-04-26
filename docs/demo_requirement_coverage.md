# Demo Requirement Coverage

| Official video requirement | Demo location | Evidence file/page | Status | Fix applied |
|---|---|---|---|---|
| Problem and target user | Main page hero + Video Roadmap | `/`, `frontend/src/App.tsx` | PASS | Main page includes target user, problem, scope chips, and official requirement coverage. |
| Architecture | Hero system strip + Pipeline View | `/#session-story`, `docs/architecture_overview.md` | PASS | Main page shows the five-component pipeline and handoff explanation. |
| Main workflow end-to-end | Debug Workspace + Pipeline + Verification | `/#workspace`, `cases/bug_case_02_name_error.py`, `/api/run` | PASS | Main page supports happy-path loading, run action, pipeline, and result cards. |
| Coordination / branching / agent interaction | Pipeline and Session Explorer | `/#session-story`, `/#explorer`, `trace.jsonl` artifacts | PASS | Main page includes handoff cards, active pipeline states, trace event cards, and retry attempts. |
| Evidence layer / logs / traces / outputs | Session Explorer tabs | `/#explorer`, `outputs/sessions/`, `evaluation/runs/20260425T180442Z/` | PASS | Main page includes trace, diff, retry, verifier, and artifact panels. |
| Failure / limitation / boundary behavior | Failure Analysis | `/#evaluation`, `evaluation/failure_log.md`, `docs/phase3_failure_analysis.md` | PASS | Main page includes superficial-fix and no-oracle boundary cards. |
| Final output / artifact / export | Final Output & Evidence Package | `/#final-output`, `evaluation/evaluation_results.csv`, `evaluation/failure_log.md` | PASS | Main page includes final contribution, limitations, manual items, and artifact paths. |
| Mostly actual project rather than slides | Main frontend page | `/`, visual API, real cases/evaluation files | PASS | The main page uses the live visual API and repository artifacts. |
| Real 5-minute video artifact | Video file and index | `media/tracefix_phase3_demo.mp4`, `media/demo_video_link.txt` | PASS | Added the supplied MP4 to the repository and documented it in the video index. |
| Screenshot files for final report | Screenshot folder/index | `docs/screenshots/`, `docs/screenshots/screenshot_index.md` | PASS | Seven final report screenshots are included and indexed. |
| AI full response logs | AI logs folder | `docs/ai_logs/` | PARTIAL | Disclosure and appendix exist; exported full-response logs still need team attachment. |
