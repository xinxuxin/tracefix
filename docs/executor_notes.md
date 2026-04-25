# Executor Notes

## What the Executor Does

The TraceFix executor is the bounded execution component for single-file Python scripts. It accepts the current code string and optional user-facing context, writes the code into a temporary file, runs it in a local Python subprocess, and returns a structured execution record.

Its evidence includes:

- exit code
- stdout
- stderr
- traceback text when available
- timeout status
- execution duration
- temporary file path used for the run
- outcome label such as `normal_completion`, `syntax_error`, or `runtime_exception`

## What the Executor Does Not Do

The executor does not diagnose the root cause in depth. It does not modify code, choose a final fix, judge semantic correctness, or retry on its own. Those responsibilities belong to later components such as the diagnoser, patcher, verifier, and controller.

## How the Evidence Supports Later Components

The diagnoser depends on the executor's structured evidence to identify whether a failure looks like a syntax error, a missing resource, or a generic runtime exception. The verifier depends on the same structure to compare one run against another in a reproducible way.

Because the executor returns stable labels and raw stderr/traceback text, later components can reason about failures without re-implementing subprocess handling.

## Safety Boundaries

This executor is deliberately conservative for a course prototype:

- runs only Python code in a temporary working directory
- requires a timeout
- invokes Python with isolated mode `-I` when configured
- disables bytecode writes with `-B` when configured
- passes a minimal subprocess environment containing `PYTHONIOENCODING=utf-8`
- assumes no internet access and blocks simple network patterns before execution
- does not install packages
- does not invoke arbitrary shell pipelines
- can block simple out-of-scope behaviors such as network access or subprocess spawning
- returns structured failure records instead of crashing when execution cannot proceed safely

The policy gate lives in [src/tracefix/sandbox/policy.py](/Users/macbook/Desktop/agentic/src/tracefix/sandbox/policy.py). It currently blocks socket/network imports, subprocess imports, shell execution helpers, dynamic `eval`/`exec`, selected destructive filesystem operations, `shutil`, and direct access to sensitive absolute paths.

## Structured Logging

The executor writes structured JSONL trace events for:

- execution start
- execution end
- policy-blocked execution

These trace events include session id, temporary file path, duration, interpreter used, and outcome label. This makes the component easier to inspect during demos and evaluation.

## Current Limitations

- The sandbox is lightweight and process-based, not a hardened security sandbox.
- Policy blocking is pattern-based and intentionally simple.
- Pattern blocking is not a defense against adversarial obfuscation.
- The default production target is Python 3.11; if it is unavailable, the executor reports `unsupported_environment`.
- The executor does not validate semantic correctness or user intent.
- File system access inside the temporary working directory is still possible unless blocked by the script itself.
