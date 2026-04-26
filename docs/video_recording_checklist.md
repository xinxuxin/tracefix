# Video Recording Checklist

Use this checklist immediately before recording the Phase 3 project video.

## Preflight

- Run `PYTHONPATH=src python -m tracefix visual-server --port 8123`.
- Open `http://127.0.0.1:8123/`.
- Confirm the top navigation includes `Video Roadmap`, `Workspace`, `Pipeline`, `Explorer`, `Evaluation`, and `Final Output`.
- Confirm the evaluation dashboard shows 7 cases.
- Confirm failure cards mention superficial fix and ambiguous behavior.
- Confirm `media/demo_video_link.txt` is still treated as manual until a real link is pasted.

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

- Upload the video to the team-approved location.
- Replace `TODO_FOR_TEAM_ADD_VIDEO_LINK` in `media/demo_video_link.txt` with the real URL.
- Add recording date, presenter(s), and cases shown.
- Capture 4 to 8 screenshots listed in `docs/screenshots/screenshot_index.md`.
- Attach exported AI full-response logs under `docs/ai_logs/` if required for submission.
