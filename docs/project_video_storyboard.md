# Project Video Storyboard

This storyboard maps the official Phase 3 video requirements to the actual frontend main page and repository evidence.

| Time | Screen | Presenter action | Key message | Evidence |
|---|---|---|---|---|
| 0:00-0:30 | Main page hero + Video Roadmap | Open `/` and start at `#demo-roadmap` | TraceFix helps Python learners debug small scripts without trusting plausible patches blindly. | `frontend/src/App.tsx` |
| 0:30-1:10 | Hero system strip + Pipeline section | Scroll to `#session-story` | Five components separate execution, diagnosis, patching, verification, and orchestration. | `frontend/src/App.tsx`, `docs/architecture_overview.md` |
| 1:10-1:40 | Debug Workspace | Show `bug_case_02_name_error.py` source | The happy path starts with a real NameError-style typo. | `cases/bug_case_02_name_error.py` |
| 1:40-2:30 | Debug Workspace + Pipeline + Verification | Click `Run TraceFix` | TraceFix runs, patches, reruns, and accepts only when behavior matches `10.70`. | `/api/run`, `outputs/sessions/` |
| 2:30-3:20 | Session Explorer | Show trace, diff, verifier, artifacts tabs | The system preserves coordination and decision evidence. | `trace.jsonl`, `session_state.json`, `summary.md` |
| 3:20-4:20 | Failure Analysis | Show superficial and ambiguous cases | TraceFix stops or escalates when evidence is insufficient. | `evaluation/failure_log.md`, `docs/phase3_failure_analysis.md` |
| 4:20-4:45 | Evaluation Dashboard | Show seven-case table | Phase 3 evidence includes at least five cases and at least two failure cases. | `evaluation/evaluation_results.csv` |
| 4:45-5:00 | Final Output | Show artifact paths and contribution cards | Final contribution is a bounded, evidence-backed debugging workflow. | `evaluation/runs/20260425T180442Z/` |

## Backup Shot List

- If live frontend run is slow, use the latest saved session visible on the main page.
- If the frontend cannot start, use CLI fallback in `docs/demo_click_path.md`.
- Do not claim the video link is complete until `media/demo_video_link.txt` contains a real URL.
