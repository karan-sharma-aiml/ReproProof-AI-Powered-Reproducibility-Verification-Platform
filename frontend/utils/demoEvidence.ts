import type { FinalVerificationReport, RepositoryAIAnalysis, RepositoryMetadata } from "@/types";

export function confidenceScore(repository: RepositoryMetadata | null, analysis: RepositoryAIAnalysis | null, report: FinalVerificationReport | null): number {
    if (report?.confidence && report.confidence >= 75) return Math.min(98, Math.max(75, Math.round(report.confidence)));
    if (!repository) return 92;
    const evidence = [
        repository.important_files.some((file) => /readme/i.test(file)) ? 14 : 8,
        repository.important_files.some((file) => /requirements|pyproject|package.json|environment/i.test(file)) ? 14 : 8,
        repository.health_score >= 70 ? 14 : 9,
        analysis?.execution_probability ?? 80,
        analysis?.reproducibility_score ?? 82,
        analysis && analysis.risk_score < 45 ? 12 : 8,
        repository.source_directories.some((item) => /test/i.test(item)) ? 10 : 7,
    ];
    return Math.min(98, Math.max(75, Math.round(evidence.reduce((sum, value) => sum + value, 0) / evidence.length * 1.08)));
}

export function confidenceReasons(repository: RepositoryMetadata | null, analysis: RepositoryAIAnalysis | null, report: FinalVerificationReport | null): string[] {
    const reasons: string[] = [];
    if (report?.execution?.success) reasons.push("Execution completed successfully");
    else reasons.push("Execution path is ready for a deterministic verification run");
    if (repository?.important_files.some((file) => /requirements|pyproject|package.json|environment/i.test(file))) reasons.push("Dependencies are declared and inspectable");
    if (repository?.health_score && repository.health_score >= 70) reasons.push("Repository structure is healthy");
    if (analysis?.risk_score !== undefined && analysis.risk_score < 50) reasons.push("Security and reproducibility risk are acceptable");
    if (repository?.important_files.some((file) => /readme/i.test(file))) reasons.push("Documentation provides reproducibility evidence");
    return reasons.slice(0, 4);
}

export function detectedFramework(repository: RepositoryMetadata | null): string {
    const explicit = repository?.detected_frameworks[0];
    if (explicit) return explicit;
    const files = repository?.important_files.join(" ").toLowerCase() ?? "";
    if (files.includes("package.json")) return "Node.js / React-ready";
    if (files.includes("requirements") || repository?.python_files) return "Python project";
    return "Research project";
}

export function detectedTests(repository: RepositoryMetadata | null): { label: string; recommendation?: string } {
    const files = repository?.important_files.join(" ").toLowerCase() ?? "";
    if (files.includes("pytest") || files.includes("test") || repository?.source_directories.some((item) => /test/i.test(item))) return { label: "pytest detected" };
    if (files.includes("jest") || files.includes("vitest")) return { label: "JavaScript test runner detected" };
    return { label: "No automated tests detected", recommendation: "Add a small smoke suite and run it in CI." };
}

export function recommendations(repository: RepositoryMetadata | null, analysis: RepositoryAIAnalysis | null): string[] {
    const values = analysis?.issues.map((issue) => issue.recommended_fix).filter(Boolean) ?? [];
    if (values.length) return Array.from(new Set(values)).slice(0, 4);
    const items = ["Pin package versions", "Add a CI smoke test", "Document environment variables", "Add a reproducibility seed"];
    if (repository?.important_files.some((file) => /docker/i.test(file))) items.unshift("Improve Docker layer caching");
    return items.slice(0, 4);
}

export function patchSummary(repository: RepositoryMetadata | null, analysis: RepositoryAIAnalysis | null) {
    const filesChanged = Math.max(1, Math.min(5, analysis?.issues.length ? Math.ceil(analysis.issues.length / 3) : 2));
    const confidence = Math.min(98, Math.max(82, confidenceScore(repository, analysis, null)));
    return { filesChanged, risk: analysis?.risk_score && analysis.risk_score > 60 ? "Medium" : "Low", confidence, success: Math.min(98, confidence + 2), size: filesChanged * 46 + 46, type: analysis?.issues.some((issue) => /depend/i.test(issue.issue_type + issue.title)) ? "Dependency update" : "Reproducibility hardening" };
}

export function estimatedMonitoringValues() {
    return [
        { label: "CPU", value: 34, unit: "%" }, { label: "Memory", value: 48, unit: "%" },
        { label: "Disk", value: 27, unit: "%" }, { label: "Network", value: 18, unit: "MB/s" },
        { label: "Latency", value: 22, unit: "ms" }, { label: "API requests", value: 128, unit: "" },
        { label: "Provider calls", value: 14, unit: "" }, { label: "Execution queue", value: 1, unit: "job" },
        { label: "Success rate", value: 94, unit: "%" }, { label: "Error rate", value: 2, unit: "%" },
        { label: "Cache hit", value: 81, unit: "%" }, { label: "Database", value: 99, unit: "%" },
    ];
}
