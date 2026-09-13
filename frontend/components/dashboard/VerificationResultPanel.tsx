"use client";

import type { FinalVerificationReport } from "@/types";

export function VerificationResultPanel({ report, error }: { report: FinalVerificationReport | null; error: string | null }) {
    if (!report) {
        return <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Final verification</p><p className="mt-4 text-sm text-slate-500">{error ?? "Run verification to generate a final report."}</p></section>;
    }

    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const repositoryId = report.repository.repository_id;
    const matchedMetrics = Object.entries(report.verification.matched_metrics ?? {});
    const failedMetrics = Object.entries(report.verification.failed_metrics ?? {});
    const executionMetadata = Object.entries(report.execution ?? {});

    return <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between gap-3">
            <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Final verification</p>
                <p className="mt-1 text-lg font-bold text-slate-900 dark:text-white">{report.verdict}</p>
            </div>
            <div className="text-right">
                <p className="text-2xl font-bold text-brand-600 dark:text-brand-400">{report.confidence ?? 0}</p>
                <p className="text-xs text-slate-500">confidence</p>
            </div>
        </div>
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">{report.explanation}</p>

        <div className="mt-4 grid grid-cols-3 gap-2">
            <Score label="Similarity" value={report.verification.overall_similarity} />
            <Score label="Score" value={report.overall_score} />
            <Score label="Risk exposure" value={report.static_analysis.risk_score} />
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2">
            <section className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Matched metrics</p>
                <div className="mt-2 space-y-2 text-sm">
                    {matchedMetrics.length ? matchedMetrics.map(([name, value]) => <div key={name} className="flex justify-between"><span className="text-slate-500">{name}</span><span className="font-mono font-semibold text-emerald-700 dark:text-emerald-300">{value}</span></div>) : <span className="text-slate-500">None</span>}
                </div>
            </section>
            <section className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Failed metrics</p>
                <div className="mt-2 space-y-2 text-sm">
                    {failedMetrics.length ? failedMetrics.map(([name, value]) => <div key={name} className="flex justify-between"><span className="text-slate-500">{name}</span><span className="font-mono font-semibold text-rose-700 dark:text-rose-300">{value}</span></div>) : <span className="text-slate-500">None</span>}
                </div>
            </section>
        </div>

        <section className="mt-4 rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Execution metadata</p>
            <div className="mt-2 space-y-2 text-sm">
                {executionMetadata.length ? executionMetadata.map(([key, value]) => <div key={key} className="flex justify-between border-b border-slate-100 py-1 dark:border-slate-800"><span className="text-slate-500">{key}</span><span className="font-mono font-semibold text-slate-900 dark:text-white">{String(value)}</span></div>) : <span className="text-slate-500">No execution metadata</span>}
            </div>
        </section>

        <div className="mt-5 space-y-2 text-sm">
            {Object.entries(report.metrics).map(([name, value]) => <div key={name} className="flex justify-between border-b border-slate-100 py-2 dark:border-slate-800"><span className="text-slate-500">{name}</span><span className="font-mono font-semibold text-slate-900 dark:text-white">{value}</span></div>)}
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
            <a className="rounded-lg bg-brand-600 px-3 py-2 text-xs font-semibold text-white" href={`${apiBase}/report/${repositoryId}`} target="_blank">Download JSON</a>
            <a className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200" href={`${apiBase}/report/${repositoryId}/markdown`} target="_blank">Download Markdown</a>
            <a className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200" href={`${apiBase}/report/${repositoryId}/pdf`} target="_blank">Download PDF</a>
        </div>
    </section>;
}

function Score({ label, value }: { label: string; value: number }) {
    return <div className="text-center"><div className="text-lg font-bold text-slate-900 dark:text-white">{Math.round(value)}</div><div className="text-[10px] text-slate-500">{label}</div><div className="mt-1 h-1 rounded-full bg-slate-200 dark:bg-slate-700"><div className="h-full rounded-full bg-brand-500" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div></div>;
}