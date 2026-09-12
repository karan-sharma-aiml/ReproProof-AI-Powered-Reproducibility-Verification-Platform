"use client";

import { Check, GitPullRequest, Loader2, ShieldAlert } from "lucide-react";
import type { PatchResult } from "@/types";
import { DiffViewer, GlassCard, QuickActionPanel, StatusBadge } from "@/components/ui/EnterprisePrimitives";

interface PatchPreviewCardProps {
    patch: PatchResult | null;
    isGenerating: boolean;
    error: string | null;
    onGenerate: () => void;
    onApply: () => void;
    onRerun: () => void;
    onRollback: () => void;
    isApplying: boolean;
    isRerunning: boolean;
    isRollingBack: boolean;
    rollbackAvailable: boolean;
    currentStatus: string;
}

export function PatchPreviewCard({ patch, isGenerating, error, onGenerate, onApply, onRerun, onRollback, isApplying, isRerunning, isRollingBack, rollbackAvailable, currentStatus }: PatchPreviewCardProps) {
    return (
        <GlassCard>
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                    <GitPullRequest className="mt-1 h-6 w-6 text-brand-500" />
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Patch preview</p>
                        <h2 className="mt-1 text-lg font-bold text-slate-950 dark:text-white">Generated change proposal</h2>
                    </div>
                </div>
                <button
                    type="button"
                    onClick={onGenerate}
                    disabled={isGenerating}
                    className="inline-flex items-center gap-2 rounded-xl bg-blue-500 px-3 py-2 text-xs font-semibold text-white shadow-lg shadow-blue-500/20 transition hover:-translate-y-0.5 hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {isGenerating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <GitPullRequest className="h-3.5 w-3.5" />}
                    {isGenerating ? "Generating" : "Generate preview"}
                </button>
            </div>

            {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}
            {currentStatus && <div className="mt-4"><StatusBadge label={currentStatus} tone={currentStatus === "PATCH_APPLIED" ? "success" : "neutral"} /></div>}
            {!patch ? (
                <p className="mt-5 text-sm text-slate-500 dark:text-slate-400">Generate a reviewable patch from the diagnosed execution failure.</p>
            ) : (
                <>
                    <div className="mt-5 grid gap-3 sm:grid-cols-3">
                        <Metric label="Patch confidence" value={`${Math.round(patch.confidence * 100)}%`} />
                        <Metric label="Risk level" value={patch.risk_level} />
                        <Metric label="Changed files" value={String(patch.changed_files.length)} />
                    </div>
                    <p className="mt-5 text-sm text-slate-600 dark:text-slate-300">{patch.summary}</p>
                    {patch.warnings.length > 0 && (
                        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
                            <div className="flex items-center gap-2 font-semibold"><ShieldAlert className="h-4 w-4" /> Review warnings</div>
                            <ul className="mt-2 space-y-1">{patch.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
                        </div>
                    )}
                    <div className="mt-5"><p className="mb-2 text-xs font-semibold text-slate-400">{patch.file_name || "No file selected"}</p><DiffViewer diff={patch.git_unified_diff} /></div>
                    <p className="mt-4 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400"><Check className="h-3.5 w-3.5 text-emerald-500" /> Nothing has been applied to the repository.</p>
                    <QuickActionPanel>
                        <button type="button" onClick={onApply} disabled={isApplying || isRerunning || !patch.git_unified_diff || currentStatus === "PATCH_APPLIED"} className="rounded-xl bg-emerald-500 px-3 py-2 text-xs font-semibold text-white shadow-lg shadow-emerald-500/15 transition hover:-translate-y-0.5 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50">{isApplying ? "Applying" : "Apply fix"}</button>
                        <button type="button" onClick={onRerun} disabled={isRerunning || isApplying || !rollbackAvailable} className="rounded-xl bg-blue-500 px-3 py-2 text-xs font-semibold text-white shadow-lg shadow-blue-500/15 transition hover:-translate-y-0.5 hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-50">{isRerunning ? "Running" : "Run again"}</button>
                        <button type="button" onClick={onRollback} disabled={isRollingBack || isRerunning || !rollbackAvailable} className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-amber-300/30 hover:bg-amber-400/10 disabled:cursor-not-allowed disabled:opacity-50">{isRollingBack ? "Rolling back" : "Rollback"}</button>
                    </QuickActionPanel>
                </>
            )}
        </GlassCard>
    );
}

function DiffLine({ line }: { line: string }) {
    const className = line.startsWith("+") && !line.startsWith("+++")
        ? "text-emerald-300"
        : line.startsWith("-") && !line.startsWith("---")
            ? "text-rose-300"
            : line.startsWith("@@")
                ? "text-cyan-300"
                : "text-slate-400";
    return <div className={className}>{line || " "}</div>;
}

function Metric({ label, value }: { label: string; value: string }) {
    return <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-950"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{value}</p></div>;
}
