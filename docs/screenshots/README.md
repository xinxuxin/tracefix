# Screenshot Evidence

This folder tracks final screenshot evidence for Phase 3 submission. Several full-page screenshots are already present, and [screenshot_index.md](screenshot_index.md) lists the final named 4-8 screenshots recommended for the report or slide deck.

Recommended capture flow:

1. Start the local visual server: `PYTHONPATH=src python -m tracefix visual-server --port 8123`
2. Start the frontend dev server from `frontend/`: `npm run dev`
3. Load a successful sample case such as `bug_case_02_name_error`.
4. Run TraceFix and capture the workspace, pipeline, trace, diff, verifier, evaluation, and failure-analysis sections.

The frontend is evidence for the visualization layer only. The source-of-truth artifacts remain the CLI/evaluation outputs in `outputs/sessions/` and `evaluation/runs/`.
