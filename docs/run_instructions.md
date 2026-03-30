# Run Instructions

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Optional frontend setup:

```bash
cd frontend
npm install
cd ..
```

Optional provider SDKs:

```bash
python -m pip install -e ".[openai]"
python -m pip install -e ".[anthropic]"
```

Security note:

- Keep real API keys out of JSON config files.
- Prefer environment variables.
- If you run TraceFix interactively with provider mode enabled and the matching key is missing, the CLI will ask once with hidden input for the current session only.
- Do not commit real keys to GitHub.

## Run One Case

Name error case:

```bash
python -m tracefix debug cases/bug_case_02_name_error.py --expected-output-text "10.70"
```

Missing file case:

```bash
python -m tracefix debug cases/bug_case_04_missing_file.py --expected-output-text "Guest"
```

Superficial fix failure case:

```bash
python -m tracefix debug cases/bug_case_06_failure_superficial_fix.py --expected-output-text "Hello, TraceFix!"
```

## Run With Config File

```bash
python -m tracefix debug cases/bug_case_01_syntax_error.py \
  --config config/settings.example.json \
  --expected-output-text "A"
```

## Run Demo Script

```bash
PYTHONPATH=src python3 scripts/run_demo_case.py
```

## Run in OpenAI-Enhanced Mode

```bash
export OPENAI_API_KEY=your_key_here
export TRACEFIX_PROVIDER_MODE=openai
export TRACEFIX_ENABLE_LLM_DIAGNOSER=1
export TRACEFIX_ENABLE_LLM_PATCHER=1
python -m tracefix debug cases/bug_case_02_name_error.py --expected-output-text "10.70"
```

Use a lighter model if needed:

```bash
export TRACEFIX_PROVIDER_MODEL=gpt-4.1-mini
```

## Run in Anthropic-Enhanced Mode

```bash
export ANTHROPIC_API_KEY=your_key_here
export TRACEFIX_PROVIDER_MODE=anthropic
export TRACEFIX_ENABLE_LLM_DIAGNOSER=1
export TRACEFIX_ENABLE_LLM_PATCHER=1
python -m tracefix debug cases/bug_case_04_missing_file.py --expected-output-text "Guest"
```

## Fallback Behavior

- If provider mode is disabled, TraceFix stays fully local.
- If provider mode is enabled but the API key is missing, the system falls back to local logic.
- In interactive terminal runs, TraceFix will first offer a hidden prompt for the missing provider key and only then fall back if you leave it blank.
- If the provider SDK is missing or the provider response fails, the system falls back to local logic when fallback is enabled.
- Provider mode, model name, fallback usage, and provider errors are recorded in session artifacts and trace payloads.

## Run the Visual Frontend

Backend adapter only:

```bash
PYTHONPATH=src python -m tracefix visual-server --port 8123
```

Frontend development server:

```bash
cd frontend
npm run dev
```

Then open:

```text
http://127.0.0.1:5173
```

## Run the Visual Frontend in Built Static Mode

Build:

```bash
cd frontend
npm run build
cd ..
```

Serve both API and static assets from the TraceFix CLI:

```bash
PYTHONPATH=src python -m tracefix visual-server --port 8123
```

Then open:

```text
http://127.0.0.1:8123
```

## Run Evaluation

Full suite:

```bash
PYTHONPATH=src python3 evaluation/run_evaluation.py
```

Selected cases:

```bash
PYTHONPATH=src python3 evaluation/run_evaluation.py \
  --case-id bug_case_02_name_error \
  --case-id bug_case_05_runtime_exception \
  --case-id bug_case_07_failure_ambiguous_behavior
```

## Run Tests

All tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Focused controller and evaluation tests:

```bash
PYTHONPATH=src python -m unittest tests.test_controller_flow tests.test_evaluation_runner -v
```

Focused visual adapter test:

```bash
PYTHONPATH=src python -m unittest tests.test_visual_api -v
```

Focused provider/fallback tests:

```bash
PYTHONPATH=src python -m unittest tests.test_provider_modes tests.test_cli_runtime_prompt -v
```

## Output Locations

Single-case debug sessions:

- `outputs/sessions/<case>_<session_id>/trace.jsonl`
- `outputs/sessions/<case>_<session_id>/session_state.json`
- `outputs/sessions/<case>_<session_id>/summary.md`
- `outputs/sessions/<case>_<session_id>/failure_summary.md` when unresolved
- `outputs/sessions/<case>_<session_id>/patches/`

Evaluation runs:

- `evaluation/runs/<timestamp>/evaluation_results.csv`
- `evaluation/runs/<timestamp>/failure_cases.csv`
- `evaluation/runs/<timestamp>/run_summary.md`
- `evaluation/runs/<timestamp>/cases/<case_id>/`

Visual frontend:

- reads and surfaces the latest session under `outputs/sessions/`
- reads and surfaces the latest evaluation run under `evaluation/runs/`
- does not replace CLI outputs
