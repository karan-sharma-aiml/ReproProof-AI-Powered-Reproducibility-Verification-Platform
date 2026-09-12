"use client";

import { useEffect, useState } from "react";
import { Activity, Box, Database, HardDrive, Radio } from "lucide-react";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Health = { name: string; status: string; configured: boolean; connected: boolean; latency_ms: number; reason: string };
type Overview = { application: Health; database: Health; cache: Health; storage: Health; monitoring: Health; containers: Health; };
function displayStatus(status: string) { return status === "unavailable" ? "Standby" : status; }

export default function InfrastructurePage() {
    const [overview, setOverview] = useState<Overview | null>(null);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => { fetch(`${apiBase}/infrastructure/status`, { cache: "no-store" }).then((response) => { if (!response.ok) throw new Error(`Infrastructure request failed: ${response.status}`); return response.json() as Promise<Overview>; }).then(setOverview).catch((reason: Error) => setError(reason.message)); }, []);
    const items = overview ? [["Application", overview.application, Activity], ["Database", overview.database, Database], ["Cache", overview.cache, Radio], ["Storage", overview.storage, HardDrive], ["Monitoring", overview.monitoring, Activity], ["Containers", overview.containers, Box]] as const : [];
    return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100 lg:px-12"><div className="mx-auto max-w-7xl"><header className="border-b border-white/10 pb-8"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Infrastructure plane</p><h1 className="mt-3 text-4xl font-semibold tracking-tight">Production foundations</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">Database, cache, storage, monitoring, and container readiness from the same provider-neutral health contracts.</p></header>{error ? <p className="mt-8 text-sm text-rose-300">{error}</p> : <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{items.map(([label, item, Icon]) => <div key={label} className="border border-white/10 bg-white/[0.03] p-5"><div className="flex items-center justify-between"><Icon className="h-5 w-5 text-cyan-300" /><span className={`text-xs uppercase tracking-wider ${item.status === "healthy" ? "text-emerald-300" : item.status === "unavailable" ? "text-slate-500" : "text-amber-300"}`}>{displayStatus(item.status)}</span></div><h2 className="mt-5 font-semibold">{label}</h2><p className="mt-2 text-sm text-slate-500">{item.reason || "Provider health is being sampled."}</p><div className="mt-5 flex justify-between border-t border-white/10 pt-3 text-xs text-slate-500"><span>{item.configured ? "configured" : "local fallback"}</span><span>{item.latency_ms.toFixed(1)} ms</span></div></div>)}</section>}</div></main>;
}
