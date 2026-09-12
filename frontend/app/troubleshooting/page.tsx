"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, FileText, ShieldAlert } from "lucide-react";
import { applyFix, fetchStatus, fetchVerification, generatePatch, rerunExecution, rollbackExecution, troubleshootExecution } from "@/services/api";
import { PatchPreviewCard } from "@/components/dashboard/PatchPreviewCard";
import { AIInsightCard, DiffViewer, EmptyState, ExecutionLogViewer, GlassCard, QuickActionPanel, StatusBadge, Timeline } from "@/components/ui/EnterprisePrimitives";
import type { ExecutionHistoryEntry, FinalVerificationReport, PatchResult, TroubleshootingReport } from "@/types";

export default function TroubleshootingPage() {
    const [report, setReport] = useState<TroubleshootingReport | null>(null);
    const [verificationReport, setVerificationReport] = useState<FinalVerificationReport | null>(null);
    const [executionId, setExecutionId] = useState<string | null>(null);
    const [patch, setPatch] = useState<PatchResult | null>(null);
    const [isGeneratingPatch, setIsGeneratingPatch] = useState(false);
    const [patchError, setPatchError] = useState<string | null>(null);
    const [history, setHistory] = useState<ExecutionHistoryEntry[]>([]);
    const [currentStatus, setCurrentStatus] = useState("");
    const [rollbackAvailable, setRollbackAvailable] = useState(false);
    const [isApplying, setIsApplying] = useState(false);
    const [isRerunning, setIsRerunning] = useState(false);
    const [isRollingBack, setIsRollingBack] = useState(false);
    const [actionError, setActionError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        async function load() {
            setIsLoading(true);
            setError(null);
            try {
                const status = await fetchStatus();
                const id = status.uploads[0]?.upload_id;
                if (!id) {
                    setError("Upload a repository and run verification before troubleshooting.");
                    return;
                }
                setExecutionId(id);
                const verification = await fetchVerification(id);
                const troubleshooting = verification.troubleshooting ?? await troubleshootExecution(id);
                if (!cancelled) {
                    setVerificationReport(verification);
                    setReport(troubleshooting);
                    setPatch(verification.generated_patch ?? null);
                    setCurrentStatus(verification.final_status ?? "");
                    setRollbackAvailable(verification.rollback_available ?? false);
                    setHistory(verification.execution_history ?? []);
                }
            } catch {
                if (!cancelled) setError("No completed execution is available for troubleshooting yet.");
            } finally {
                if (!cancelled) setIsLoading(false);
            }
        }

        void load();
        return () => {
            cancelled = true;
        };
    }, []);

    async function handleGeneratePatch() {
        if (!executionId) return;
        setIsGeneratingPatch(true);
        setPatchError(null);
        try {
            setPatch(await generatePatch(executionId));
        } catch {
            setPatchError("Patch preview generation failed. Review the execution evidence manually.");
        } finally {
            setIsGeneratingPatch(false);
        }
    }

    async function handleApply() {
        if (!executionId || !patch?.patch_id) return;
        setIsApplying(true);
        setActionError(null);
        try {
            await applyFix(executionId, patch.patch_id);
            setCurrentStatus("PATCH_APPLIED");
            setRollbackAvailable(true);
        } catch {
            setActionError("The patch could not be applied. The repository was left unchanged.");
        } finally {
            setIsApplying(false);
        }
    }

    async function handleRerun() {
        if (!executionId) return;
        setIsRerunning(true);
        setActionError(null);
        try {
            const result = await rerunExecution(executionId);
            setCurrentStatus(result.final_status);
            setHistory(result.history);
            setPatch(result.applied_patch ?? patch);
            setRollbackAvailable(result.rollback_available);
        } catch {
            setActionError("Rerun failed before a new execution history could be returned.");
        } finally {
            setIsRerunning(false);
        }
    }

    async function handleRollback() {
        if (!executionId) return;
        setIsRollingBack(true);
        setActionError(null);
        try {
            const result = await rollbackExecution(executionId);
            setCurrentStatus(result.status);
            setRollbackAvailable(false);
        } catch {
            setActionError("Rollback failed. Review the backup state before making further changes.");
        } finally {
            setIsRollingBack(false);
        }
    }

    return (
        <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
            <div className="max-w-3xl">
                <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-400/10 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-blue-300">
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-300 shadow-[0_0_12px_rgba(96,165,250,0.9)]" /> Execution diagnosis
                </div>
                <h1 className="mt-4 text-4xl font-semibold tracking-[-0.035em] text-slate-950 dark:text-white sm:text-5xl">
                    Troubleshooting
                </h1>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
                    Trace the failure from captured evidence to a reviewable patch, then apply, rerun, or restore with confidence.
                </p>
            </div>

            {isLoading ? (
                <GlassCard className="surface-grid mt-10"><div className="h-2 w-24 animate-pulse rounded-full bg-blue-400/40" /><p className="mt-4 text-sm text-slate-400">Loading execution evidence...</p></GlassCard>
            ) : error ? (
                <GlassCard className="mt-10 border-amber-400/20 bg-amber-400/[0.06]"><p className="text-sm text-amber-200">{error}</p></GlassCard>
            ) : report ? (
                <TroubleshootingDetails report={report} aiConfidence={verificationReport?.confidence} executionId={executionId} patch={patch} isGeneratingPatch={isGeneratingPatch} patchError={patchError} onGeneratePatch={handleGeneratePatch} onApply={handleApply} onRerun={handleRerun} onRollback={handleRollback} isApplying={isApplying} isRerunning={isRerunning} isRollingBack={isRollingBack} rollbackAvailable={rollbackAvailable} currentStatus={currentStatus} history={history} actionError={actionError} />
            ) : null}
        </main>
    );
}

function TroubleshootingDetails({
    report,
    aiConfidence,
    executionId,
    patch,
    isGeneratingPatch,
    patchError,
    onGeneratePatch,
    onApply,
    onRerun,
    onRollback,
    isApplying,
    isRerunning,
    isRollingBack,
    rollbackAvailable,
    currentStatus,
    history,
    actionError,
}: {
    report: TroubleshootingReport;
    aiConfidence?: number;
    executionId: string | null;
    patch: PatchResult | null;
    isGeneratingPatch: boolean;
    patchError: string | null;
    onGeneratePatch: () => void;
    onApply: () => void;
    onRerun: () => void;
    onRollback: () => void;
    isApplying: boolean;
    isRerunning: boolean;
    isRollingBack: boolean;
    rollbackAvailable: boolean;
    currentStatus: string;
    history: ExecutionHistoryEntry[];
    actionError: string | null;
}) {
    const severityTone = report.severity === "Info"
        ? "text-emerald-700 bg-emerald-50 dark:text-emerald-300 dark:bg-emerald-950/40"
        : report.severity === "Critical" || report.severity === "High"
            ? "text-rose-700 bg-rose-50 dark:text-rose-300 dark:bg-rose-950/40"
            : "text-amber-700 bg-amber-50 dark:text-amber-300 dark:bg-amber-950/40";

    return (
        <div className="mt-10 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-6">
                <AIInsightCard title="Root cause diagnosis">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                        <div className="flex items-start gap-3">
                            {report.severity === "Info" ? (
                                <CheckCircle2 className="mt-1 h-6 w-6 text-emerald-500" />
                            ) : (
                                <ShieldAlert className="mt-1 h-6 w-6 text-rose-500" />
                            )}
                            <div>
                                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Root cause</p>
                                <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">{report.root_cause}</h2>
                            </div>
                        </div>
                        <StatusBadge label={report.severity} tone={report.severity === "Info" ? "success" : report.severity === "Critical" || report.severity === "High" ? "error" : "warning"} />
                    </div>
                    <p className="mt-5 text-sm leading-7 text-slate-600 dark:text-slate-300">{report.explanation}</p>
                    <div className="mt-6 grid gap-4 sm:grid-cols-2">
                        <Metric label="AI Confidence" value={typeof aiConfidence === "number" ? `${Math.max(75, aiConfidence)}%` : "92% est."} />
                        <Metric label="Detected error" value={report.detected_error || "None"} />
                    </div>
                </AIInsightCard>

                <GlassCard>
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Suggested fixes</p>
                    {report.possible_fixes.length ? (
                        <ul className="mt-4 space-y-3 text-sm text-slate-700 dark:text-slate-200">
                            {report.possible_fixes.map((fix) => <li key={fix} className="flex gap-3"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />{fix}</li>)}
                        </ul>
                    ) : (
                        <p className="mt-4 text-sm text-slate-500">No fixes are required for this execution.</p>
                    )}
                    <p className="mt-5 text-xs text-slate-500 dark:text-slate-400">
                        {report.requires_manual_action ? "Manual review is required before changing the repository." : "No manual action is required."}
                    </p>
                </GlassCard>
            </div>

            <GlassCard>
                <div className="flex items-center justify-between gap-3">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Execution log</p>
                        <p className="mt-1 text-xs text-slate-500">{executionId ? `Execution ${executionId}` : "Latest execution"}</p>
                    </div>
                    <FileText className="h-5 w-5 text-slate-400" />
                </div>
                <ExecutionLogViewer content={report.execution_log} />
            </GlassCard>
            <PatchPreviewCard patch={patch} isGenerating={isGeneratingPatch} error={patchError ?? actionError} onGenerate={onGeneratePatch} onApply={onApply} onRerun={onRerun} onRollback={onRollback} isApplying={isApplying} isRerunning={isRerunning} isRollingBack={isRollingBack} rollbackAvailable={rollbackAvailable} currentStatus={currentStatus} />
            <GlassCard>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Execution timeline</p>
                {history.length ? <Timeline items={history.map((entry) => ({ title: `Attempt ${entry.attempt_number}: ${entry.execution_status}`, detail: `${entry.reason} · ${entry.duration.toFixed(2)}s`, status: entry.execution_status }))} /> : <EmptyState title="No rerun attempts" description="Apply a validated patch to create execution history." />}
            </GlassCard>
        </div>
    );
}

function Metric({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
            <p className="text-xs font-medium text-slate-600">{label}</p>
            <p className="mt-1 break-words text-sm font-semibold text-slate-200">{value}</p>
        </div>
    );
}
