"use client";

import { motion } from "framer-motion";
import { Activity, ArrowUpRight, BrainCircuit, GitBranch, ShieldCheck, Sparkles } from "lucide-react";
import ReactFlow, { Background, Controls, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { GlassCard, StatusBadge } from "@/components/ui/EnterprisePrimitives";
import type { PlatformOverview } from "@/types";

const accentClasses = {
    emerald: { glow: "bg-emerald-400/[0.08]", icon: "text-emerald-300" },
    cyan: { glow: "bg-cyan-400/[0.08]", icon: "text-cyan-300" },
    violet: { glow: "bg-violet-400/[0.08]", icon: "text-violet-300" },
    amber: { glow: "bg-amber-400/[0.08]", icon: "text-amber-300" },
} as const;

export function EnterpriseOverview({ repositoryName, isRunning, overview }: { repositoryName?: string; isRunning: boolean; overview: PlatformOverview | null }) {
    const repositoryScore = overview?.scores.repository_score;
    const confidence = overview ? Math.round(overview.confidence * 100) : null;
    const risk = overview?.scores.security === undefined ? null : Math.round(100 - overview.scores.security);
    const activeAgents = overview?.workflow.filter((item) => item.status === "active").length ?? 0;
    const liveStats = [
        { label: "Repository health", value: repositoryScore === undefined ? "--" : String(Math.round(repositoryScore)), suffix: "/100", detail: overview ? "Judge evidence" : "Waiting for repository", icon: ShieldCheck, accent: "emerald" },
        { label: "AI confidence", value: confidence === null ? "--" : String(confidence), suffix: "%", detail: overview ? overview.verdict : "Awaiting evaluation", icon: BrainCircuit, accent: "cyan" },
        { label: "Active agents", value: overview ? String(activeAgents).padStart(2, "0") : "--", suffix: overview ? ` / ${String(overview.workflow.length).padStart(2, "0")}` : "", detail: isRunning ? "Live workflow" : "Workflow ready", icon: Activity, accent: "violet" },
        { label: "Risk exposure", value: risk === null ? "--" : String(risk), suffix: "/100", detail: overview ? `${overview.recommendations.length} recommendations` : "Evidence pending", icon: Sparkles, accent: "amber" },
    ];
    const graphNodes: Node[] = overview?.workflow.map((item, index) => ({ id: item.id, position: { x: 24 + (index % 4) * 128, y: 54 + Math.floor(index / 4) * 90 }, data: { label: item.label }, type: "default" })) ?? [];
    const graphEdges: Edge[] = overview?.workflow.slice(1).map((item, index) => ({ id: `${overview.workflow[index].id}-${item.id}`, source: overview.workflow[index].id, target: item.id, animated: item.status === "active" })) ?? [];
    const profileData = overview ? Object.entries(overview.scores).map(([label, score]) => ({ label: label.replaceAll("_", " ").slice(0, 12), score: Math.round(score), confidence: Math.round(overview.confidence * 100) })) : [];
    return (
        <section className="mb-8 space-y-5">
            <div className="flex flex-wrap items-end justify-between gap-5">
                <div>
                    <p className="mb-3 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300"><span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" /> Live intelligence layer</p>
                    <h2 className="text-3xl font-semibold tracking-[-0.04em] text-white sm:text-4xl">Good morning, operator.</h2>
                    <p className="mt-2 text-sm text-slate-400">{repositoryName ? `Monitoring ${repositoryName} across the verification graph.` : "Your research control plane is ready for its next artifact."}</p>
                </div>
                <div className="flex items-center gap-2"><StatusBadge label={isRunning ? "Workflow running" : "Systems nominal"} tone={isRunning ? "warning" : "success"} /><span className="text-xs text-slate-500">Updated just now</span></div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {liveStats.map((stat, index) => <motion.article key={stat.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.06 }} className="group relative overflow-hidden rounded-2xl border border-white/[0.09] bg-slate-950/60 p-5 backdrop-blur-xl"><div className={`absolute -right-8 -top-8 h-24 w-24 rounded-full ${accentClasses[stat.accent as keyof typeof accentClasses].glow} blur-2xl`} /><div className="relative flex items-start justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">{stat.label}</p><p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-white">{stat.value}<span className="text-base text-slate-500">{stat.suffix}</span></p><p className="mt-2 text-xs text-slate-400">{stat.detail}</p></div><stat.icon className={`h-5 w-5 ${accentClasses[stat.accent as keyof typeof accentClasses].icon}`} /></div></motion.article>)}
            </div>
            <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
                <GlassCard className="min-h-[290px] overflow-hidden border-white/[0.09] bg-slate-950/55 p-0"><div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4"><div><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Judge evidence</p><h3 className="mt-1 text-sm font-semibold text-white">Evaluation profile</h3></div><button type="button" className="rounded-lg p-2 text-slate-500 hover:bg-white/[0.06] hover:text-white" title="Open analytics"><ArrowUpRight className="h-4 w-4" /></button></div><div className="h-[220px] px-2 pb-2 pt-5"><ResponsiveContainer width="100%" height="100%"><AreaChart data={profileData}><defs><linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#34d399" stopOpacity={0.28} /><stop offset="100%" stopColor="#34d399" stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="rgba(148,163,184,.09)" vertical={false} /><XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 9 }} axisLine={false} tickLine={false} /><YAxis domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={28} /><Tooltip contentStyle={{ background: "#0f172a", border: "1px solid rgba(255,255,255,.12)", borderRadius: 10, color: "#e2e8f0", fontSize: 12 }} /><Area type="monotone" dataKey="score" stroke="#34d399" strokeWidth={2} fill="url(#scoreFill)" /></AreaChart></ResponsiveContainer></div></GlassCard>
                <GlassCard className="min-h-[290px] border-white/[0.09] bg-slate-950/55 p-0"><div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4"><div><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Agent topology</p><h3 className="mt-1 text-sm font-semibold text-white">Workflow graph</h3></div><GitBranch className="h-4 w-4 text-cyan-300" /></div><div className="h-[238px]"><ReactFlow nodes={graphNodes} edges={graphEdges} fitView panOnDrag={false} zoomOnScroll={false} nodesDraggable={false} proOptions={{ hideAttribution: true }}><Background color="#334155" gap={20} size={1} /><Controls showInteractive={false} /></ReactFlow></div></GlassCard>
            </div>
        </section>
    );
}
