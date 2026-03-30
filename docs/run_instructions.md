# Run Instructions

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

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
