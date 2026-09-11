# ReproProof QA Demo

Tiny research demo used to validate the complete ReproProof workflow.

Expected metric: accuracy = 94.2
Tolerance: 0.5

The entry point intentionally imports `qa_missing_dependency` so the sandbox produces a recoverable ModuleNotFoundError.
