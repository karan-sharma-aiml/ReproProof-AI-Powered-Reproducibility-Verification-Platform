"use client";

import { useEffect, useState } from "react";
import { Activity, BarChart3, CheckCircle2, Clock3, Cpu, ShieldCheck, TriangleAlert } from "lucide-react";
import { fetchAnalytics, fetchExecutiveSummary, fetchHealthScore, fetchStatus } from "@/services/api";
import { usePlatformProgress } from "@/hooks/usePlatformProgress";
import { GlassCard, MetricCard, RepositoryHealthCard, Timeline } from "@/components/ui/EnterprisePrimitives";
import { StatCard } from "@/components/ui/StatCard";
import type { AnalyticsResult, ExecutiveSummary, HealthScoreResult } from "@/types";

export default function AnalyticsPage() {
    const [analytics, setAnalytics] = useState<AnalyticsResult | null>(null);
    const [health, setHealth] = useState<HealthScoreResult | null>(null);
    const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
    const [executionId, setExecutionId] = useState<string>();
    const [error, setError] = useState<string | null>(null);
    const { events, latest } = usePlatformProgress(executionId);

    useEffect(() => {
        async function load() {
            try {
                const [metrics, status] = await Promise.all([fetchAnalytics(), fetchStatus()]);
                setAnalytics(metrics);
                const id = status.uploads[0]?.upload_id;
                if (id) {
                    setExecutionId(id);
                    const [score, executive] = await Promise.all([fetchHealthScore(id), fetchExecutiveSummary(id)]);
                    setHealth(score);
                    setSummary(executive);
                }
            } catch {
                setError("Analytics are unavailable until a verification run has completed.");
            }
        }
        void load();
    }, []);

    return <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
        <div className="flex flex-wrap items-end justify-between gap-5">
            <div><p className="text-sm font-semibold uppercase tracking-[0.16em] text-violet-400">Platform intelligence</p><h1 className="mt-3 text-4xl font-bold tracking-tight text-white">Analytics</h1><p className="mt-3 text-slate-300">A clear view of reproducibility outcomes across the current workspace.</p></div>
            {latest && <GlassCard className="min-w-56 border-violet-400/20 bg-violet-500/[0.08]"><div className="flex items-center justify-between text-xs font-semibold text-violet-200"><span className="flex items-center gap-2"><Activity className="h-4 w-4" /> Live progress</span><span>{latest.progress}%</span></div><p className="mt-2 text-sm font-semibold text-white">{latest.message}</p><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full bg-violet-400 transition-all" style={{ width: `${latest.progress}%` }} /></div></GlassCard>}
        </div>
        {error ? <p className="mt-8 rounded-xl border border-amber-400/30 bg-amber-400/10 p-5 text-sm text-amber-300">{error}</p> : <>
            <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Kpi icon={BarChart3} label="Total runs" value={analytics?.total_runs ?? 0} /><Kpi icon={CheckCircle2} label="Successful" value={analytics?.successful_runs ?? 0} tone="green" /><Kpi icon={Clock3} label="Average runtime" value={`${(analytics?.average_runtime ?? 0).toFixed(1)}s`} tone="cyan" /><Kpi icon={ShieldCheck} label="AI confidence" value={`${Math.round(analytics?.average_ai_confidence ?? 0)}%`} tone="violet" /></div>
            <div className="mt-6 grid gap-6 lg:grid-cols-[1.15fr_0.85fr]"><GlassCard><h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Executive summary</h2><p className="mt-5 text-lg leading-8 text-slate-200">{summary?.summary ?? "Complete a run to generate an executive summary."}</p><div className="mt-6 flex flex-wrap gap-3"><Badge label={`Health ${health?.score ?? 0}/100`} /><Badge label={`Patch success ${Math.round(analytics?.patch_success_rate ?? 0)}%`} /><Badge label={`Retry success ${Math.round(analytics?.retry_success_rate ?? 0)}%`} /></div></GlassCard><RepositoryHealthCard score={health?.score ?? 0} recommendations={health?.recommendations} /></div>
            <div className="mt-6 grid gap-6 lg:grid-cols-2"><Distribution title="Root causes" values={analytics?.most_common_root_causes ?? {}} color="bg-brand-500" /><Distribution title="Framework distribution" values={analytics?.framework_distribution ?? {}} color="bg-cyan-500" /><Distribution title="Languages" values={analytics?.language_distribution ?? {}} color="bg-emerald-500" /><Distribution title="Common errors" values={analytics?.most_common_errors ?? {}} color="bg-amber-500" /></div>
            <GlassCard className="mt-6"><h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Live execution timeline</h2><div className="mt-5">{events.length ? <Timeline items={events.map((event) => ({ title: event.stage, detail: `${event.message} · ${new Date(event.timestamp).toLocaleTimeString()}`, status: event.status }))} /> : <p className="text-sm text-slate-500">Waiting for live platform events for the latest execution.</p>}</div></GlassCard>
        </>}
    </main>;
}

function Kpi({ icon: Icon, label, value, tone = "violet" }: { icon: typeof Activity; label: string; value: string | number; tone?: "violet" | "green" | "cyan" }) { return <StatCard icon={Icon} label={label} value={String(value)} description="Workspace signal" tone={tone} />; }
function Badge({ label }: { label: string }) { return <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider bg-slate-400/10 text-slate-200">{label}</span>; }
function HealthCard({ health }: { health: HealthScoreResult | null }) { return <RepositoryHealthCard score={health?.score ?? 0} recommendations={health?.recommendations} />; }
function Distribution({ title, values, color }: { title: string; values: Record<string, number>; color: string }) { const max = Math.max(1, ...Object.values(values)); return <GlassCard><p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">{title}</p><div className="mt-5 space-y-4">{Object.entries(values).length ? Object.entries(values).map(([name, value]) => <div key={name}><div className="mb-1 flex justify-between text-xs"><span className="truncate text-slate-300">{name}</span><span className="font-semibold text-white">{value}</span></div><div className="h-2 rounded-full bg-white/10"><div className={`h-full rounded-full ${color}`} style={{ width: `${(value / max) * 100}%` }} /></div></div>) : <p className="text-sm text-slate-500">No data yet.</p>}</div></GlassCard>; }