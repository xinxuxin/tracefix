# Demo Click Path

This click path uses commands already documented in the repository and the frontend package scripts.

## Start Commands

From the repository root:

```bash
PYTHONPATH=src python -m tracefix visual-server --port 8123
```

In a second terminal, either use the built frontend served by the visual server:

```text
http://127.0.0.1:8123/
```

Or use Vite during development:

```bash
cd frontend
npm run dev
```

Then open:

```text
http://127.0.0.1:5173/
```

## Recording Click Path

1. Open `/`.
2. Show the hero section and `Video Roadmap` for problem, target user, scope chips, and the official coverage checklist.
3. Scroll to `Pipeline` and explain Controller, Executor, Diagnoser, Patcher, Verifier.
4. Scroll to `Workspace`.
5. Confirm `bug_case_02_name_error.py` is shown.
6. Click `Run TraceFix`.
7. Wait for the final decision card to show `accept`.
8. Show pipeline progression, attempts used, and behavior match.
9. Scroll to `Explorer`.
10. Open one trace event disclosure.
11. Show patch diff, verifier result, and artifact paths.
12. Scroll to `Evaluation` and focus on `Failure Analysis`.
13. Explain `bug_case_06_failure_superficial_fix` and `bug_case_07_failure_ambiguous_behavior`.
14. Show the evaluation dashboard.
15. Show seven cases and highlighted failure/boundary rows.
16. End at `Final Output` with artifact paths, contribution, limitations, and manual submission items.

## Fallback CLI Path

If frontend recording fails, use:

```bash
python -m tracefix debug cases/bug_case_02_name_error.py --expected-output-text "10.70"
PYTHONPATH=src python3 evaluation/run_evaluation.py
```

Then show:

- `outputs/sessions/<latest>/summary.md`
- `outputs/sessions/<latest>/trace.jsonl`
- `outputs/sessions/<latest>/session_state.json`
- `evaluation/evaluation_results.csv`
- `evaluation/failure_log.md`

The fallback still uses the actual project; it just loses the frontend visualization layer.
