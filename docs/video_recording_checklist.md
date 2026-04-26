# Video Recording Checklist

Use this checklist immediately before recording the Phase 3 project video.

## Preflight

- Run `PYTHONPATH=src python -m tracefix visual-server --port 8123`.
- Open `http://127.0.0.1:8123/`.
- Confirm the top navigation includes `Video Roadmap`, `Workspace`, `Pipeline`, `Explorer`, `Evaluation`, and `Final Output`.
- Confirm the evaluation dashboard shows 7 cases.
- Confirm failure cards mention superficial fix and ambiguous behavior.
- Confirm `media/tracefix_phase3_demo.mp4` exists, or record a replacement video if the team wants a newer take.

## During Recording

- Keep the video mostly on the actual frontend, not slides.
- Click `Run TraceFix` for `bug_case_02_name_error.py`.
- Show the final decision `accept`.
- Show at least one trace event payload.
- Show the patch diff and verifier rationale.
- Show artifact paths.
- Show at least one failure/boundary case.
- Show the evaluation table.

## After Recording

- Upload `media/tracefix_phase3_demo.mp4` to Canvas or the team-approved location.
- If Canvas requires a hosted URL, paste that URL into `media/demo_video_link.txt`.
- Add recording date, presenter(s), and cases shown.
- Capture 4 to 8 screenshots listed in `docs/screenshots/screenshot_index.md`.
- Attach exported AI full-response logs under `docs/ai_logs/` if required for submission.
