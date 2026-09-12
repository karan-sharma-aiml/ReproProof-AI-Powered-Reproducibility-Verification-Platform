"""Deterministic root-cause detection for execution evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.troubleshooter.models import ParsedExecution, RootCauseFinding
from app.services.confidence_engine import ConfidenceEngine


@dataclass(frozen=True)
class _Rule:
    category: str
    pattern: re.Pattern[str]
    severity: str
    evidence_strength: float
    fix: str


class RootCauseAnalyzer:
    """Detect likely failure causes using ordered, explainable rules."""

    _RULES = (
        # ─── Critical Errors (Exit immediately) ───────────────────────────
        _Rule(
            "SyntaxError",
            re.compile(r"\bSyntaxError\b|IndentationError", re.I),
            "High",
            0.99,
            "Correct the reported source syntax before rerunning.",
        ),
        _Rule(
            "ModuleNotFoundError",
            re.compile(r"ModuleNotFoundError|No module named", re.I),
            "High",
            0.98,
            "Declare and install the missing package with a compatible pinned version.",
        ),
        _Rule(
            "PermissionError",
            re.compile(r"\bPermissionError\b|permission denied", re.I),
            "High",
            0.98,
            "Review filesystem permissions and the execution identity.",
        ),
        _Rule(
            "Timeout",
            re.compile(r"TimeoutExpired|timed out|timeout", re.I),
            "High",
            0.99,
            "Measure workload duration and review the bounded execution timeout.",
        ),
        # ─── Import and Dependency Errors ──────────────────────────────────
        _Rule(
            "ImportError",
            re.compile(r"\bImportError\b|cannot import name|from .* import", re.I),
            "High",
            0.96,
            "Verify the import target and dependency version compatibility.",
        ),
        _Rule(
            "Package Version Conflict",
            re.compile(
                r"incompatible|conflict|requires .*but .* is installed|version conflict|version mismatch",
                re.I,
            ),
            "High",
            0.90,
            "Pin compatible package versions and regenerate the isolated environment.",
        ),
        # ─── File and I/O Errors ───────────────────────────────────────────
        _Rule(
            "FileNotFoundError",
            re.compile(
                r"\bFileNotFoundError\b|No such file or directory|cannot find path",
                re.I,
            ),
            "High",
            0.97,
            "Verify the path and ensure the required repository or dataset file is present.",
        ),
        _Rule(
            "Dataset Missing",
            re.compile(
                r"dataset|data file|\.csv|\.json|\.parquet|\.xlsx|\.pickle", re.I
            ),
            "High",
            0.86,
            "Confirm the dataset is included and that the configured path matches the execution working directory.",
        ),
        # ─── Type and Value Errors ─────────────────────────────────────────
        _Rule(
            "TypeError",
            re.compile(r"\bTypeError\b", re.I),
            "Medium",
            0.96,
            "Inspect the failing call and align argument and value types with the function contract.",
        ),
        _Rule(
            "ValueError",
            re.compile(r"\bValueError\b", re.I),
            "Medium",
            0.96,
            "Validate the input value and the expected format at the reported traceback location.",
        ),
        _Rule(
            "AttributeError",
            re.compile(r"\bAttributeError\b", re.I),
            "Medium",
            0.96,
            "Verify the object type and attribute name at the reported traceback location.",
        ),
        # ─── Configuration and Environment ─────────────────────────────────
        _Rule(
            "Missing Environment Variables",
            re.compile(
                r"environment variable|os\.environ|KeyError: ['\"][A-Z0-9_]+['\"]|undefined.*variable",
                re.I,
            ),
            "High",
            0.88,
            "Document and provide the required environment variables through the approved runtime configuration.",
        ),
        _Rule(
            "Configuration Errors",
            re.compile(r"configuration|config file|settings|invalid.*config", re.I),
            "Medium",
            0.78,
            "Review configuration files, defaults, and runtime-specific settings.",
        ),
        # ─── Database Errors ───────────────────────────────────────────────
        _Rule(
            "Database Connection Error",
            re.compile(
                r"database|connection.*refused|could not connect|connection.*failed|sqlalchemy|psycopg|pymongo|redis",
                re.I,
            ),
            "High",
            0.85,
            "Verify database connection string, credentials, host availability, and database initialization.",
        ),
        _Rule(
            "SQL Error",
            re.compile(
                r"sql|query error|syntax error.*sql|table.*not.*found|column.*not.*found",
                re.I,
            ),
            "High",
            0.80,
            "Check SQL syntax, table schema, and column names in your queries.",
        ),
        # ─── Network and API Errors ────────────────────────────────────────
        _Rule(
            "Network Error",
            re.compile(
                r"connection|connection.*timeout|network|socket|host.*unreachable|unable to resolve",
                re.I,
            ),
            "High",
            0.82,
            "Verify network connectivity, DNS resolution, and remote service availability.",
        ),
        _Rule(
            "API Error",
            re.compile(
                r"api|http error|status code|request.*failed|endpoint|authorization|401|403|404|500",
                re.I,
            ),
            "Medium",
            0.75,
            "Check API endpoint URL, authentication credentials, and remote service status.",
        ),
        # ─── Memory and Resource Errors ────────────────────────────────────
        _Rule(
            "Memory Error",
            re.compile(
                r"\bMemoryError\b|out of memory|MemoryError|not enough memory", re.I
            ),
            "High",
            0.98,
            "Reduce data size, optimize memory usage, or increase available system memory.",
        ),
        _Rule(
            "Disk Space Error",
            re.compile(r"disk space|no space left|disk full", re.I),
            "High",
            0.98,
            "Free up disk space or optimize temporary file generation.",
        ),
        # ─── OS and Platform Errors ────────────────────────────────────────
        _Rule(
            "Unsupported OS",
            re.compile(
                r"operating system|platform not supported|winerror|posix-only|unsupported .*platform",
                re.I,
            ),
            "Medium",
            0.84,
            "Use a supported runtime or replace the platform-specific dependency or path.",
        ),
        # ─── Runtime and Logic Errors ──────────────────────────────────────
        _Rule(
            "RuntimeError",
            re.compile(r"\bRuntimeError\b", re.I),
            "High",
            0.95,
            "Review the complete traceback and runtime state before proposing a code change.",
        ),
        _Rule(
            "IndexError",
            re.compile(r"\bIndexError\b|list.*out of range|index.*out of bounds", re.I),
            "Medium",
            0.95,
            "Verify array/list bounds and index access patterns in the failing code.",
        ),
        _Rule(
            "KeyError",
            re.compile(r"\bKeyError\b|key.*not found|dictionary.*key", re.I),
            "Medium",
            0.95,
            "Verify dictionary keys and access patterns in the failing code.",
        ),
        _Rule(
            "ZeroDivisionError",
            re.compile(r"\bZeroDivisionError\b|division by zero", re.I),
            "High",
            0.98,
            "Add validation to prevent division by zero values.",
        ),
        # ─── Import and Module Errors ──────────────────────────────────────
        _Rule(
            "Circular Dependency",
            re.compile(r"circular.*import|cyclic.*dependency|import.*cycle", re.I),
            "Medium",
            0.88,
            "Refactor imports to eliminate circular dependencies.",
        ),
        # ─── Catch-all Rules ───────────────────────────────────────────────
        _Rule(
            "Assertion Failure",
            re.compile(r"\bAssertionError\b|assert.*failed", re.I),
            "Medium",
            0.90,
            "Review the failing assertion and validate input data/state.",
        ),
        _Rule(
            "Exception",
            re.compile(r"\bException\b|error occurred|raised exception", re.I),
            "Medium",
            0.50,
            "Check the exception message and stack trace for root cause details.",
        ),
    )

    def analyze(self, evidence: ParsedExecution) -> list[RootCauseFinding]:
        if evidence.exit_code == 0 and not evidence.stderr and not evidence.traceback:
            return []
        text = "\n".join(
            (
                evidence.stderr,
                evidence.stdout,
                evidence.traceback,
                evidence.execution_log,
            )
        )
        findings: list[RootCauseFinding] = []
        for rule in self._RULES:
            match = rule.pattern.search(text)
            if match:
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                evidence_lines = [line for line in lines if rule.pattern.search(line)][
                    :3
                ] or lines[:3]
                findings.append(
                    RootCauseFinding(
                        category=rule.category,
                        evidence=evidence_lines,
                        finding_confidence=ConfidenceEngine.finding_confidence(
                            rule.evidence_strength
                        ),
                        severity=rule.severity,
                    )
                )
        if not findings:
            findings.append(
                RootCauseFinding(
                    category="Unknown",
                    evidence=[f"exit_code={evidence.exit_code}"],
                    finding_confidence=ConfidenceEngine.finding_confidence(0.25),
                    severity="High",
                )
            )
        return findings

    def fixes(self, findings: list[RootCauseFinding]) -> list[str]:
        return list(
            dict.fromkeys(self._fix_for(finding.category) for finding in findings)
        )

    @staticmethod
    def _fix_for(category: str) -> str:
        for rule in RootCauseAnalyzer._RULES:
            if rule.category == category:
                return rule.fix
        return "Review the complete execution evidence and investigate the failure manually."
