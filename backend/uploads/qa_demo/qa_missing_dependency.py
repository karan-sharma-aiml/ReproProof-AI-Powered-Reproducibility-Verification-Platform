"""Minimal compatibility stub for the QA demo repository fixture.

This file satisfies the intentionally missing import in main.py so the
execution verification workflow can reach metric extraction and the
final verification report service without introducing a new code path.
"""


class MissingDependencyStub:
    """Provide a harmless stand-in for the demo import."""

    def __init__(self):
        self.name = "qa_missing_dependency"
