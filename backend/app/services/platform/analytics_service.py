"""Aggregate analytics from the existing in-memory report and history stores."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from app.models.final_verification_report import FinalVerificationReport
from app.services.self_healing.models import ExecutionHistoryEntry
from app.services.platform.models import AnalyticsResult


class AnalyticsService:
    """Build dashboard metrics without changing report storage semantics."""

    def summarize(
        self,
        reports: Iterable[FinalVerificationReport],
        history: Iterable[ExecutionHistoryEntry] = (),
    ) -> AnalyticsResult:
        report_list = list(reports)
        history_list = list(history)
        successful = [report for report in report_list if report.execution.success]
        failed = [report for report in report_list if not report.execution.success]
        causes = Counter(
            report.troubleshooting.root_cause
            for report in report_list
            if report.troubleshooting and report.troubleshooting.root_cause
        )
        errors = Counter(
            report.troubleshooting.detected_error
            for report in report_list
            if report.troubleshooting and report.troubleshooting.detected_error
        )
        missing = Counter()
        for report in report_list:
            if report.troubleshooting:
                for finding in report.troubleshooting.findings:
                    if finding.category == "ModuleNotFoundError":
                        for evidence in finding.evidence:
                            missing[evidence] += 1
        languages = Counter(
            language
            for report in report_list
            for language in report.repository.detected_languages
        )
        frameworks = Counter(
            framework
            for report in report_list
            for framework in report.repository.detected_frameworks
        )
        patched = [report for report in report_list if report.applied_patch]
        retries = [entry for entry in history_list if entry.attempt_number > 1]
        retry_successes = [
            entry
            for entry in retries
            if entry.execution_status in {"COMPLETED", "SUCCESS"}
        ]
        return AnalyticsResult(
            total_runs=len(report_list),
            successful_runs=len(successful),
            failed_runs=len(failed),
            average_runtime=(
                (
                    sum(report.execution.execution_time for report in report_list)
                    / len(report_list)
                )
                if report_list
                else 0
            ),
            average_ai_confidence=(
                (
                    sum(report.final_ai_confidence for report in report_list)
                    / len(report_list)
                )
                if report_list
                else 0
            ),
            patch_success_rate=(
                (
                    sum(report.execution.success for report in patched)
                    / len(patched)
                    * 100
                )
                if patched
                else 0
            ),
            retry_success_rate=(
                (len(retry_successes) / len(retries) * 100) if retries else 0
            ),
            most_common_errors=dict(errors.most_common(10)),
            most_common_root_causes=dict(causes.most_common(10)),
            top_missing_dependencies=dict(missing.most_common(10)),
            language_distribution=dict(languages),
            framework_distribution=dict(frameworks),
            repository_statistics={
                "average_files": (
                    (
                        sum(report.repository.total_files for report in report_list)
                        / len(report_list)
                    )
                    if report_list
                    else 0
                ),
                "average_health": (
                    (
                        sum(report.repository.health_score for report in report_list)
                        / len(report_list)
                    )
                    if report_list
                    else 0
                ),
            },
        )
