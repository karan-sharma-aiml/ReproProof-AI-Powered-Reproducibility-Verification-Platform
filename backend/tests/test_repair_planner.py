"""Comprehensive smoke tests for RepairPlanner."""

from __future__ import annotations

import unittest

from app.models.error_analysis import ErrorAnalysis
from app.services.repair_planner import RepairPlanner


def analysis(category: str, evidence: list[str] | None = None) -> ErrorAnalysis:
    return ErrorAnalysis(
        category=category,
        root_cause=f"Observed {category}",
        severity="high" if category != "None" else "none",
        repairable=category != "None",
        confidence=96,
        evidence=evidence or [category],
        suggested_repair_type="deterministic test input",
    )


class RepairPlannerSmokeTest(unittest.TestCase):
    def test_maps_all_supported_error_categories(self) -> None:
        expected = {
            "ModuleNotFoundError": "INSTALL_DEPENDENCY",
            "ImportError": "INSTALL_DEPENDENCY",
            "FileNotFoundError": "FIX_DATASET_PATH",
            "SyntaxError": "REVIEW_SOURCE_CODE",
            "PermissionError": "CHECK_PERMISSIONS",
            "TimeoutExpired": "INCREASE_TIMEOUT",
            "MemoryError": "REDUCE_MEMORY_USAGE",
            "AssertionError": "REVIEW_SOURCE_CODE",
            "RuntimeError": "MANUAL_INVESTIGATION",
            "OSError": "MANUAL_INVESTIGATION",
            "None": "NO_ACTION_REQUIRED",
        }
        planner = RepairPlanner()

        for category, repair_type in expected.items():
            with self.subTest(category=category):
                plan = planner.create_plan(analysis(category))
                self.assertEqual(plan.repair_type, repair_type)
                self.assertGreaterEqual(plan.confidence, 0)
                self.assertLessEqual(plan.confidence, 100)

    def test_extracts_missing_module_without_executing_install(self) -> None:
        plan = RepairPlanner().create_plan(
            analysis(
                "ModuleNotFoundError",
                ["ModuleNotFoundError: No module named 'pandas'"],
            )
        )

        self.assertEqual(plan.suggested_commands, ["pip install pandas"])
        self.assertFalse(plan.safe_to_apply)
        self.assertTrue(plan.requires_human_review)

    def test_handles_unknown_category_as_manual_investigation(self) -> None:
        plan = RepairPlanner().create_plan(analysis("Unknown"))

        self.assertEqual(plan.repair_type, "MANUAL_INVESTIGATION")
        self.assertEqual(plan.suggested_commands, [])
        self.assertTrue(plan.requires_human_review)

    def test_success_requires_no_action(self) -> None:
        plan = RepairPlanner().create_plan(analysis("None"))

        self.assertEqual(plan.suggested_commands, [])
        self.assertEqual(plan.manual_actions, [])
        self.assertTrue(plan.safe_to_apply)
        self.assertFalse(plan.requires_human_review)


if __name__ == "__main__":
    unittest.main()
