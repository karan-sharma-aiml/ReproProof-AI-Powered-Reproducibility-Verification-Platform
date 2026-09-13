# Runtime Execution Fix Report

## Root Cause

The repository was detected and planned correctly, but `SandboxExecutionEngine._stream_process()` treated every command as a finite batch process. Uvicorn is intentionally long-running, so the monitor waited for it to exit until the generic timeout, terminated it, returned `TIMEOUT` or `SUBPROCESS_FAILED` with `success=False`, and emitted `EXECUTION_FAILED`.

`routes.py` then mapped `result.success` directly to the terminal SSE event:

- `VERIFICATION_READY` with `SUCCESS` when `result.success` was true
- `VERIFICATION_READY` with `FAILED` when it was false

The exact failure was therefore after `SERVER_STARTED`, when the healthy server was incorrectly handled as a process that had to exit.

## Fix

Server commands (`uvicorn`, Flask, and Django server commands) now use a dedicated lifecycle:

1. Start the process and log PID, working directory, command, and port.
2. Allocate a local port when one was not supplied.
3. Retry `/health`, then `/`, with exponential delays.
4. Retry connection refusal and HTTP 503 responses until the startup timeout.
5. Emit `HEALTH_CHECK_SUCCESS` only after an HTTP response is received.
6. Collect stdout/stderr evidence.
7. Gracefully terminate the server after evidence collection.
8. Return `success=True`, `status=EXECUTION_COMPLETE`, and `timed_out=False`.

Windows environments without a `uvicorn.exe` shim now launch it through `py -m uvicorn`.

The SSE route emits successful terminal stages after a successful result:

- `EXECUTION_COMPLETE`
- `REPORT_GENERATED`
- `VERIFICATION_READY` with `SUCCESS`

## Additional Fix

The planner now selects a root-level `app.py` for FastAPI projects instead of incorrectly falling back to `main.py`.

## Validation

- Backend suite: `80 passed, 1 skipped, 28 subtests passed`
- Runtime/SSE regression: Uvicorn starts, health responds, graceful termination occurs, and no `EXECUTION_FAILED` is emitted after startup.
- Real ReproProof repository: detected as `Monorepo`, frontend `Next.js`, backend `fastapi (Python)`, execution target `backend`, entry point `app/main.py`.
- Touched files: no diagnostics reported.

The three external GitHub repositories were not executed in this local validation run because they were not cloned into the workspace during this session. Their repository-specific dependency installation and application entry-point behavior require a network clone and potentially substantial setup; the new runtime path is covered by the local FastAPI integration tests.
