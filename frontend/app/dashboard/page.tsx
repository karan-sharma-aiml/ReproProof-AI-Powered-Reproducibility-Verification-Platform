"use client";

import { Activity, Database, FileCheck2, RefreshCw } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { RecentProjectsCard } from "@/components/cards/RecentProjectsCard";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ProgressTimeline } from "@/components/dashboard/ProgressTimeline";
import { LogsPanel } from "@/components/dashboard/LogsPanel";
import { useHealth } from "@/hooks/useHealth";
import { useStatus } from "@/hooks/useStatus";
import { useRepository } from "@/hooks/useRepository";
import { useRepositoryAnalysis } from "@/hooks/useRepositoryAnalysis";
import { useExecutionStream } from "@/hooks/useExecutionStream";
import { useVerification } from "@/hooks/useVerification";
import { ExecutionMonitor } from "@/components/dashboard/ExecutionMonitor";
import { VerificationResultPanel } from "@/components/dashboard/VerificationResultPanel";
import type { RepositoryMetadata, TimelineEntry } from "@/types";

export default function DashboardPage() {
    const { health, isLoading: healthLoading, refetch: refetchHealth } = useHealth();
    const { status, isLoading: statusLoading, refetch: refetchStatus } = useStatus();
    const latestUploadId = status?.uploads[0]?.upload_id;
    const { repository, isLoading: repositoryLoading, error: repositoryError } = useRepository(latestUploadId);
    const { analysis, isLoading: analysisLoading, error: analysisError } = useRepositoryAnalysis(latestUploadId);
    const refresh = () => { refetchHealth(); refetchStatus(); };
    const timeline = buildTimeline(repository, repositoryLoading, Boolean(latestUploadId));
    const logLines = repository ? [
        `Analyzed ${repository.total_files} files and ${repository.total_folders} folders`,
        `Detected ${repository.detected_frameworks.join(", ") || "no framework"}`,
        `Found ${repository.datasets.length} dataset file(s)`,
    ] : repositoryError ? [repositoryError] : ["Waiting for an uploaded repository"];
    return <div className="mx-auto flex max-w-7xl lg:min-h-[calc(100vh-9rem)]"><Sidebar /><main className="min-w-0 flex-1 px-4 py-8 sm:px-6 lg:px-10"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-brand-600 dark:text-brand-400">Workspace overview</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 dark:text-white">Repository analysis</h1><p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Live metadata from the latest uploaded repository.</p></div><button type="button" onClick={refresh} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:border-brand-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"><RefreshCw className="h-4 w-4" /> Refresh</button></div><div className="mt-8 grid gap-4 sm:grid-cols-3"><Metric icon={Database} label="Files" value={repositoryLoading ? "-" : String(repository?.total_files ?? 0)} /><Metric icon={Activity} label="Health score" value={repositoryLoading ? "-" : `${repository?.health_score ?? 0}/100`} /><Metric icon={FileCheck2} label="Risk score" value={analysisLoading ? "-" : `${analysis?.risk_score ?? 0}/100`} /></div><div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]"><div className="space-y-6"><section id="uploads"><RecentProjectsCard uploads={status?.uploads ?? []} isLoading={statusLoading} /></section><section id="logs"><LogsPanel lines={logLines} /></section><MetadataPanel repository={repository} /><AnalysisPanel analysis={analysis} error={analysisError} /></div><div className="space-y-6"><section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><div className="mb-6 flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Current run</p><h2 className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">Analysis progress</h2></div><span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 dark:bg-brand-950 dark:text-brand-300">{repositoryLoading || analysisLoading ? "Running" : repository && analysis ? "Complete" : "Idle"}</span></div><ProgressTimeline entries={timeline} /></section><section id="health" className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Health status</p><div className="mt-4 flex items-center gap-3"><span className={`h-3 w-3 rounded-full ${repository?.health_score && repository.health_score >= 70 ? "bg-emerald-500" : "bg-amber-500"}`} /><div><p className="font-semibold text-slate-900 dark:text-white">{repository ? `${repository.health_score}/100 repository health` : "Awaiting analysis"}</p><p className="text-xs text-slate-500">{repository?.warnings.join("; ") || "No repository warnings"}</p></div>{healthLoading && <LoadingSpinner size="sm" className="ml-auto" />}</div></section></div></div></main></div>;
}

function buildTimeline(repository: RepositoryMetadata | null, loading: boolean, hasUpload: boolean): TimelineEntry[] {
    return [
        { id: "1", label: "Artifact received", status: hasUpload ? "done" : "pending" },
        { id: "2", label: "Repository analyzed", status: loading ? "running" : repository ? "done" : "pending" },
        { id: "3", label: "Project metadata detected", status: repository ? "done" : "pending" },
        { id: "4", label: "Execution verification", status: "pending" },
    ];
}

function MetadataPanel({ repository }: { repository: NonNullable<ReturnType<typeof useRepository>["repository"]> | null }) {
    const verification = useVerification(repository?.repository_id);
    const execution = useExecutionStream(repository?.repository_id, verification.fetch);
    return <><section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Detected metadata</p>{repository ? <div className="mt-4 space-y-4 text-sm"><MetadataList label="Frameworks" values={repository.detected_frameworks} /><MetadataList label="Important files" values={repository.important_files} /><MetadataList label="Source directories" values={repository.source_directories} /><MetadataList label="Datasets" values={repository.datasets} /><div><p className="mb-2 font-medium text-slate-700 dark:text-slate-200">Repository tree</p><div className="max-h-40 overflow-auto rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-500 dark:bg-slate-950 dark:text-slate-400">{repository.tree.map((entry) => <div key={entry}>{entry}</div>)}</div></div></div> : <p className="mt-4 text-sm text-slate-500">Upload a repository to see detected metadata.</p>}</section><div className="mt-6"><ExecutionMonitor repositoryId={repository?.repository_id} events={execution.events} status={execution.status} currentStage={execution.currentStage} progress={execution.progress} elapsedSeconds={execution.elapsedSeconds} isRunning={execution.isRunning} onStart={execution.start} /></div><div className="mt-6"><VerificationResultPanel report={verification.report} error={verification.error} /></div></>;
}

function MetadataList({ label, values }: { label: string; values: string[] }) { return <div><p className="font-medium text-slate-700 dark:text-slate-200">{label}</p><p className="mt-1 text-slate-500 dark:text-slate-400">{values.length ? values.join(", ") : "None detected"}</p></div>; }

function AnalysisPanel({ analysis, error }: { analysis: import("@/types").RepositoryAIAnalysis | null; error: string | null }) {
    return <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><p className="text-xs font-semibold uppercase tracking-wider text-slate-400">AI reproducibility analysis</p>{error ? <p className="mt-4 text-sm text-amber-600">{error}</p> : analysis ? <div className="mt-4 space-y-5"><div className="grid grid-cols-3 gap-2"><Score label="Execution" value={analysis.execution_probability} /><Score label="Reproducibility" value={analysis.reproducibility_score} /><Score label="Risk" value={analysis.risk_score} /></div><p className="text-sm text-slate-500 dark:text-slate-400">{analysis.summary}</p><div className="space-y-3">{analysis.issues.map((issue) => <article key={`${issue.issue_type}-${issue.title}`} className="rounded-lg border border-slate-200 p-3 dark:border-slate-700"><div className="flex items-start justify-between gap-3"><h3 className="text-sm font-semibold text-slate-900 dark:text-white">{issue.title}</h3><span className={`rounded px-2 py-0.5 text-[10px] font-bold ${severityClass(issue.severity)}`}>{issue.severity}</span></div><p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{issue.description}</p><p className="mt-2 text-xs font-medium text-brand-600 dark:text-brand-400">Fix: {issue.recommended_fix}</p></article>)}</div></div> : <p className="mt-4 text-sm text-slate-500">Upload a repository to run static analysis.</p>}</section>;
}

function Score({ label, value }: { label: string; value: number }) { return <div className="text-center"><div className="text-xl font-bold text-slate-900 dark:text-white">{value}</div><div className="text-[10px] text-slate-500">{label}</div><div className="mt-2 h-1.5 rounded-full bg-slate-200 dark:bg-slate-700"><div className={`h-full rounded-full ${value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-amber-500" : "bg-red-500"}`} style={{ width: `${value}%` }} /></div></div>; }

function severityClass(severity: import("@/types").IssueSeverity) { return severity === "CRITICAL" ? "bg-red-100 text-red-700" : severity === "HIGH" ? "bg-orange-100 text-orange-700" : severity === "MEDIUM" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600"; }

function Metric({ icon: Icon, label, value }: { icon: typeof Database; label: string; value: string }) { return <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"><Icon className="h-5 w-5 text-brand-500" /><p className="mt-4 text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p><p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">{value}</p></div>; }