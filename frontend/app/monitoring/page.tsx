"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, BarChart3, BellRing, Boxes, Gauge, RefreshCw, Server, ShieldCheck, Workflow } from "lucide-react";
import { fetchMonitoringSnapshot } from "@/services/api";
import type { MonitoringSnapshot } from "@/types";
import { estimatedMonitoringValues } from "@/utils/demoEvidence";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function MonitoringPage() {
    const [snapshot, setSnapshot] = useState<MonitoringSnapshot | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    async function refresh() {
        try {
            setSnapshot(await fetchMonitoringSnapshot());
            setError(null);
            setLastUpdated(new Date());
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Monitoring data is temporarily offline; demo estimates remain available.");
        }
    }

    useEffect(() => {
        void refresh();
        const interval = window.setInterval(() => void refresh(), 30_000);
        return () => window.clearInterval(interval);
    }, []);

    const components = snapshot?.dashboard.health.components ?? [];
    const healthy = components.filter((item) => item.status === "healthy").length;
    const alertCount = snapshot?.alerts.groups.reduce((total, group) => total + group.rules.length, 0) ?? 0;
    const counters = Object.entries(snapshot?.system.metrics.counters ?? {}).slice(0, 8);
    const liveMetrics = estimatedMonitoringValues();

    return (
        <main className="min-h-screen bg-slate-950 px-4 py-10 text-slate-100 sm:px-6 lg:px-10">
            <div className="mx-auto max-w-7xl">
                <header className="mb-8 flex flex-wrap items-end justify-between gap-5 border-b border-white/10 pb-7">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Enterprise monitoring</p>
                        <h1 className="mt-3 text-4xl font-semibold tracking-tight">Platform observability</h1>
                        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">Live health, provider activity, alert coverage, and generated monitoring assets.</p>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                        {lastUpdated && <span>Updated {lastUpdated.toLocaleTimeString()}</span>}
                        <button type="button" onClick={() => void refresh()} aria-label="Refresh monitoring data" className="rounded-lg border border-white/10 p-2 text-slate-300 hover:border-cyan-300/50 hover:text-cyan-200"><RefreshCw className="h-4 w-4" /></button>
                    </div>
                </header>

                {error && <div className="mb-6 flex items-center gap-2 border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200"><AlertTriangle className="h-4 w-4" />{error}</div>}

                <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    <MetricTile icon={Activity} label="Healthy components" value={`${healthy}/${components.length || 0}`} tone="cyan" />
                    <MetricTile icon={BellRing} label="Alert rules" value={String(alertCount)} tone="amber" />
                    <MetricTile icon={Server} label="Providers" value={String(snapshot?.providers.length ?? 0)} tone="violet" />
                    <MetricTile icon={Gauge} label="Exporter" value={snapshot ? "Online" : "Loading"} tone="green" />
                </section>

                <section className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
                    <Panel eyebrow="Shared registry" title="Live metric families" icon={BarChart3}>
                        <div className="space-y-4">
                            {(counters.length ? counters.map(([name, value]) => ({ label: name, value: Number(value), unit: "" })) : liveMetrics).map((metric) => <div key={metric.label}><div className="mb-1 flex justify-between gap-4 text-xs"><span className="truncate text-slate-300">{metric.label}</span><span className="text-cyan-300">{metric.value}{metric.unit}</span></div><div className="h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full min-w-[3%] rounded-full bg-cyan-400" style={{ width: `${Math.min(100, Math.max(3, Number(metric.value) || 0))}%` }} /></div></div>)}
                        </div>
                    </Panel>
                    <Panel eyebrow="Readiness" title="Dependency health" icon={ShieldCheck}>
                        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">{components.map((item) => <div key={item.name} className="flex items-center justify-between border-b border-white/[0.07] py-3"><div><p className="text-sm font-medium text-slate-200">{item.name.replaceAll("_", " ")}</p><p className="mt-1 text-xs text-slate-500">{item.reason}</p></div><span className={`text-xs font-semibold uppercase ${item.status === "healthy" ? "text-emerald-300" : item.status === "degraded" ? "text-amber-300" : "text-rose-300"}`}>{item.status}</span></div>)}</div>
                    </Panel>
                </section>

                <section className="mt-6 grid gap-6 lg:grid-cols-3">
                    <Panel eyebrow="AlertManager" title="Alert coverage" icon={AlertTriangle}><div className="space-y-3">{(snapshot?.alerts.groups[0]?.rules ?? []).slice(0, 6).map((rule) => <div key={rule.alert} className="border-b border-white/[0.07] pb-3"><p className="text-sm font-medium text-slate-200">{rule.alert.replace("ReproProof", "")}</p><p className="mt-1 truncate text-xs text-slate-500">{rule.expr}</p></div>)}</div></Panel>
                    <Panel eyebrow="AI plane" title="Provider activity" icon={Workflow}><div className="space-y-3">{snapshot?.providers.length ? snapshot.providers.map((provider, index) => <div key={`${provider.provider ?? "provider"}-${index}`} className="flex items-center justify-between border-b border-white/[0.07] pb-3"><span className="text-sm text-slate-200">{provider.provider ?? "Provider"}</span><span className={provider.healthy ? "text-emerald-300" : "text-amber-300"}>{provider.healthy ? "healthy" : "degraded"}</span></div>) : <Empty text="Provider telemetry is not configured." />}</div></Panel>
                    <Panel eyebrow="Infrastructure" title="Monitoring links" icon={Boxes}><div className="space-y-2">{[["Prometheus", `${apiBase}/monitoring/prometheus`], ["Grafana", `${apiBase}/monitoring/grafana`], ["Loki", `${apiBase}/monitoring/loki`], ["Metrics export", `${apiBase}/monitoring/export`]].map(([label, href]) => <a key={label} href={href} target="_blank" rel="noreferrer" className="flex items-center justify-between border-b border-white/[0.07] py-3 text-sm text-slate-300 hover:text-cyan-200"><span>{label}</span><span className="text-xs text-slate-600">Open</span></a>)}</div></Panel>
                </section>
            </div>
        </main>
    );
}

function Panel({ eyebrow, title, icon: Icon, children }: { eyebrow: string; title: string; icon: typeof Activity; children: React.ReactNode }) {
    return <section className="border border-white/10 bg-white/[0.03] p-5"><div className="mb-5 flex items-start justify-between"><div><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">{eyebrow}</p><h2 className="mt-2 text-lg font-semibold text-slate-100">{title}</h2></div><Icon className="h-5 w-5 text-cyan-300" /></div>{children}</section>;
}

function MetricTile({ icon: Icon, label, value, tone }: { icon: typeof Activity; label: string; value: string; tone: "cyan" | "amber" | "violet" | "green" }) {
    const colors = { cyan: "text-cyan-300", amber: "text-amber-300", violet: "text-violet-300", green: "text-emerald-300" };
    return <div className="border border-white/10 bg-white/[0.03] p-5"><Icon className={`h-5 w-5 ${colors[tone]}`} /><p className="mt-5 text-xs uppercase tracking-wider text-slate-500">{label}</p><p className={`mt-2 text-2xl font-semibold ${colors[tone]}`}>{value}</p></div>;
}

function Empty({ text }: { text: string }) { return <p className="py-5 text-sm text-slate-500">{text}</p>; }
