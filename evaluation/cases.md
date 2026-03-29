# Evaluation Cases

This file defines the initial evaluation set for the Stage 1 prototype.

| Case | File | Expected Outcome | Why It Matters |
| --- | --- | --- | --- |
| `name_error_typo` | `cases/name_error_bug.py` | Auto-fix succeeds | Exercises runtime diagnosis, patching, and verification |
| `missing_colon` | `cases/missing_colon_bug.py` | Auto-fix succeeds | Exercises syntax-error diagnosis and conservative rewrite |
| `unsupported_type_error` | `cases/type_error_bug.py` | Stop without patch | Demonstrates conservative escalation instead of overreaching |

Success criteria for this stage:

1. The controller produces a JSON trace for every run.
2. Supported cases finish with a saved patch artifact.
3. Unsupported cases stop with an explicit reason.
4. Unit tests cover the core flow and stop conditions.
