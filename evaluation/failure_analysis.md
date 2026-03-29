# Failure Analysis

## Current Failure Modes

### Unsupported Runtime Bugs

TraceFix currently stops on bugs such as `TypeError`, `AttributeError`, incorrect business logic, and data-dependent failures. This is intentional because the current patcher only supports a narrow set of low-risk transformations.

### Semantic Regressions

The verifier checks whether the script now executes successfully. It does not validate user intent or output correctness. A patch can therefore remove a crash without proving that the program is fully correct.

### Lightweight Sandbox Limitations

Execution happens in a temporary directory with `python -I -B` and a timeout. That reduces environmental noise and limits execution time, but it is not a hardened security sandbox.

### Python Version Sensitivity

Error messages can vary slightly across Python versions. The prototype targets Python 3.11, and diagnosis heuristics should be validated there during the final demo workflow.

## Conservative Stops

The controller stops when:

1. The original script already succeeds
2. The diagnoser cannot justify a supported bug class
3. The patcher cannot construct a conservative patch
4. Verification reproduces the same failure
5. Verification introduces a new failure and the retry budget is exhausted

