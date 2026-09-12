"use client";

import { useEffect, useState } from "react";
import { Activity, Boxes, Clock3, Cpu, Database, Gauge, Layers3, Server } from "lucide-react";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Overview = { cache: { hits: number; misses: number; hit_ratio: number; entries: number }; queue: { queued: number; running: number; workers: number; failed: number }; resources: { cpu_seconds: number; memory_bytes: number; queue_size: number; provider_latency_seconds: number }; latency: { request_seconds: number; ai_provider_seconds: number; rag_seconds: number; throughput_per_second: number; bottlenecks: string[] }; };

async function loadOverview(): Promise<Overview> {
    const response = await fetch(`${apiBase}/performance/metrics`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Performance request failed: ${response.status}`);
    return response.json() as Promise<Overview>;
}

function Metric({ icon: Icon, label, value, detail }: { icon: typeof Activity; label: string; value: string; detail: string }) {
    return <div className="border border-white/10 bg-white/[0.03] p-5"><Icon className="h-4 w-4 text-cyan-300" /><p className="mt-5 text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-white">{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></div>;
}

export default function PerformancePage() {
    const [overview, setOverview] = useState<Overview | null>(null);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => { loadOverview().then(setOverview).catch((reason: Error) => setError(reason.message)); }, []);
    const memory = overview ? `${Math.round(overview.resources.memory_bytes / 1024 / 1024)} MB` : "--";
    return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100 lg:px-12"><div className="mx-auto max-w-7xl"><header className="border-b border-white/10 pb-8"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Performance plane</p><h1 className="mt-3 text-4xl font-semibold tracking-tight">Capacity and reliability</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">Operational signals for cache efficiency, queue pressure, resource usage, and provider latency.</p></header>{error ? <p className="mt-8 text-sm text-rose-300">{error}</p> : <><section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric icon={Database} label="Cache hit ratio" value={overview ? `${Math.round(overview.cache.hit_ratio * 100)}%` : "--"} detail={overview ? `${overview.cache.entries} entries` : "Loading"} /><Metric icon={Layers3} label="Queue pressure" value={overview ? String(overview.queue.queued) : "--"} detail={overview ? `${overview.queue.running} running` : "Loading"} /><Metric icon={Cpu} label="Memory" value={memory} detail={overview ? `${overview.resources.cpu_seconds.toFixed(2)} CPU seconds` : "Loading"} /><Metric icon={Server} label="Workers" value={overview ? String(overview.queue.workers) : "--"} detail={overview ? `${overview.queue.failed} failed jobs` : "Loading"} /></section><section className="mt-6 grid gap-6 lg:grid-cols-[1fr_1fr]"><div className="border border-white/10 bg-white/[0.03] p-6"><div className="flex items-center gap-3"><Gauge className="h-5 w-5 text-emerald-300" /><h2 className="font-semibold">Latency timeline</h2></div><div className="mt-6 space-y-4">{[["API request", overview?.latency.request_seconds], ["AI provider", overview?.latency.ai_provider_seconds], ["RAG retrieval", overview?.latency.rag_seconds]].map(([label, value]) => <div key={String(label)}><div className="flex justify-between text-sm"><span className="text-slate-300">{label}</span><span className="font-mono text-slate-500">{typeof value === "number" ? `${value.toFixed(3)}s` : "--"}</span></div><div className="mt-2 h-1 bg-slate-800"><div className="h-1 bg-cyan-300" style={{ width: `${Math.min(100, Number(value ?? 0) * 100)}%` }} /></div></div>)}</div></div><div className="border border-white/10 bg-white/[0.03] p-6"><div className="flex items-center gap-3"><Activity className="h-5 w-5 text-amber-300" /><h2 className="font-semibold">Bottleneck detection</h2></div><div className="mt-6 flex items-center gap-3 text-sm text-slate-400"><Clock3 className="h-4 w-4" />{overview?.latency.bottlenecks?.join(", ") || "No bottlenecks reported"}</div><p className="mt-6 text-xs leading-5 text-slate-500">Throughput: {overview ? overview.latency.throughput_per_second.toFixed(2) : "--"} requests per second</p></div></section></>}</div></main>;
}
