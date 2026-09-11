"""Generate safe, deterministic repair strategies from error analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.core.logging import get_logger
from app.models.error_analysis import ErrorAnalysis
from app.models.repair_plan import RepairPlan

logger = get_logger("repair_planner")

RepairType = Literal[
    "INSTALL_DEPENDENCY",
    "FIX_DATASET_PATH",
    "VERIFY_ENTRY_POINT",
    "CHECK_PERMISSIONS",
    "REVIEW_SOURCE_CODE",
    "INCREASE_TIMEOUT",
    "REDUCE_MEMORY_USAGE",
    "MANUAL_INVESTIGATION",
    "NO_ACTION_REQUIRED",
]


@dataclass(frozen=True)
class _RepairRule:
    """Static strategy metadata for one analyzer category."""

    repair_type: RepairType
    description: str
    manual_actions: tuple[str, ...]
    safe_to_apply: bool
    requires_human_review: bool


class RepairPlanner:
    """Translate an ErrorAnalysis into text-only repair guidance."""

    _RULES: dict[str, _RepairRule] = {
        "ModuleNotFoundError": _RepairRule(
            "INSTALL_DEPENDENCY",
            "Install the missing dependency in the isolated environment after verifying its source and version.",
            (
                "Confirm the missing module name and select a compatible pinned package version.",
            ),
            False,
            True,
        ),
        "ImportError": _RepairRule(
            "INSTALL_DEPENDENCY",
            "Verify that the dependency and requested symbol are compatible with the project.",
            ("Check the import target and compare it with the installed package API.",),
            False,
            True,
        ),
        "FileNotFoundError": _RepairRule(
            "FIX_DATASET_PATH",
            "Verify the missing dataset or resource path before changing project configuration.",
            (
                "Verify the dataset or required file exists in the repository or mounted input.",
                "Update the project configuration to use the verified path.",
            ),
            False,
            True,
        ),
        "SyntaxError": _RepairRule(
            "REVIEW_SOURCE_CODE",
            "Review the reported Python source location and correct the syntax before rerunning.",
            (
                "Inspect the traceback location and validate the source with a syntax checker.",
            ),
            False,
            True,
        ),
        "PermissionError": _RepairRule(
            "CHECK_PERMISSIONS",
            "Inspect filesystem permissions and the identity used by the execution environment.",
            (
                "Confirm the required files and directories are readable or writable as needed.",
            ),
            False,
            True,
        ),
        "TimeoutExpired": _RepairRule(
            "INCREASE_TIMEOUT",
            "Review whether the workload is expected to exceed the configured execution timeout.",
            (
                "Measure the workload duration and increase the bounded timeout only when justified.",
            ),
            False,
            True,
        ),
        "MemoryError": _RepairRule(
            "REDUCE_MEMORY_USAGE",
            "Reduce peak memory demand or provide a larger approved execution resource.",
            (
                "Identify the largest allocations and consider batching, streaming, or smaller inputs.",
            ),
            False,
            True,
        ),
        "AssertionError": _RepairRule(
            "REVIEW_SOURCE_CODE",
            "Review the failed assertion and determine whether the code or input violates the expected invariant.",
            (
                "Inspect the assertion context and validate the expected input and output contract.",
            ),
            False,
            True,
        ),
        "RuntimeError": _RepairRule(
            "MANUAL_INVESTIGATION",
            "Investigate the runtime state and surrounding application logs before proposing a change.",
            (
                "Review the complete traceback, runtime configuration, and preceding log events.",
            ),
            False,
            True,
        ),
        "OSError": _RepairRule(
            "MANUAL_INVESTIGATION",
            "Investigate the operating-system or filesystem failure using the captured evidence.",
            (
                "Review the operating-system error details, resource availability, and filesystem state.",
            ),
            False,
            True,
        ),
        "None": _RepairRule(
            "NO_ACTION_REQUIRED",
            "Execution completed successfully and does not require a repair strategy.",
            (),
            True,
            False,
        ),
    }
    _MODULE_PATTERN = re.compile(r"No module named ['\"]([^'\"]+)['\"]", re.IGNORECASE)

    def create_plan(self, analysis: ErrorAnalysis) -> RepairPlan:
        """Create a deterministic repair plan without executing or modifying anything."""
        rule = self._RULES.get(analysis.category, self._RULES["OSError"])
        suggested_commands: list[str] = []
        manual_actions = list(rule.manual_actions)

        if rule.repair_type == "INSTALL_DEPENDENCY":
            package_name = self._missing_package(analysis)
            suggested_commands.append(f"pip install {package_name}")
            if package_name == "<missing_package>":
                manual_actions.insert(
                    0, "Identify the missing package from the full traceback."
                )

        plan = RepairPlan(
            repair_type=rule.repair_type,
            description=rule.description,
            suggested_commands=suggested_commands,
            manual_actions=manual_actions,
            confidence=analysis.confidence,
            safe_to_apply=rule.safe_to_apply,
            requires_human_review=rule.requires_human_review,
        )
        logger.info(
            "Created repair plan: category=%s repair_type=%s confidence=%d",
            analysis.category,
            plan.repair_type,
            plan.confidence,
        )
        return plan

    def _missing_package(self, analysis: ErrorAnalysis) -> str:
        evidence = "\n".join(analysis.evidence)
        match = self._MODULE_PATTERN.search(evidence)
        if not match:
            return "<missing_package>"
        package_name = match.group(1).split(".", 1)[0]
        if re.fullmatch(r"[A-Za-z0-9_.-]+", package_name):
            return package_name
        return "<missing_package>"
