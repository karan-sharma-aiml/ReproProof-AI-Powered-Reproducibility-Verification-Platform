"use client";

import { FormEvent, useEffect, useState } from "react";
import { BrainCircuit, CircleHelp, Network, Search, Sparkles } from "lucide-react";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Entity = { id: string; type: string; label: string; properties: Record<string, unknown> };
type Relation = { source: string; target: string; type: string; weight: number };
type Graph = { entities: Entity[]; relationships: Relation[] };
type Answer = { answer: string; confidence: number; evidence: string[]; citations: { title: string; quote: string; uri: string; score: number }[]; provider: string };

async function getJson<T>(path: string): Promise<T> {
    const response = await fetch(`${apiBase}${path}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json() as Promise<T>;
}

export default function KnowledgePage() {
    const [graph, setGraph] = useState<Graph>({ entities: [], relationships: [] });
    const [stats, setStats] = useState<Record<string, unknown> | null>(null);
    const [query, setQuery] = useState("");
    const [answer, setAnswer] = useState<Answer | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        Promise.all([getJson<Graph>("/knowledge/graph"), getJson<Record<string, unknown>>("/knowledge/statistics")])
            .then(([loadedGraph, loadedStats]) => { setGraph(loadedGraph); setStats(loadedStats); })
            .catch((reason: Error) => setError(reason.message));
    }, []);

    async function ask(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!query.trim()) return;
        setError(null);
        try {
            const response = await fetch(`${apiBase}/rag/query`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query, limit: 5, generate_answer: true }) });
            if (!response.ok) throw new Error(`RAG request failed: ${response.status}`);
            setAnswer(await response.json() as Answer);
        } catch (reason) { setError(reason instanceof Error ? reason.message : "RAG request failed"); }
    }

    return (
        <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100 lg:px-12">
            <div className="mx-auto max-w-7xl">
                <header className="flex flex-col justify-between gap-5 border-b border-white/10 pb-8 md:flex-row md:items-end">
                    <div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Knowledge plane</p><h1 className="mt-3 text-4xl font-semibold tracking-tight">Graph Explorer & RAG Inspector</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">Shared repository knowledge, ranked evidence, and explainable AI answers in one read-only workspace.</p></div>
                    <div className="flex gap-3 text-sm text-slate-300"><span className="border border-white/10 px-3 py-2">Entities {String(stats?.entities ?? graph.entities.length)}</span><span className="border border-white/10 px-3 py-2">Links {String(stats?.relationships ?? graph.relationships.length)}</span></div>
                </header>

                <section className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
                    <div className="border border-white/10 bg-white/[0.03] p-6">
                        <div className="flex items-center gap-3"><Network className="h-5 w-5 text-cyan-300" /><div><h2 className="font-semibold">Agent knowledge flow</h2><p className="text-xs text-slate-500">The shared graph currently contains indexed entities and workflow relations.</p></div></div>
                        <div className="mt-6 grid gap-3 sm:grid-cols-2">
                            {graph.entities.slice(0, 12).map((entity) => <div key={entity.id} className="border border-white/10 px-4 py-3"><div className="flex items-center justify-between gap-3"><span className="truncate text-sm text-slate-200">{entity.label}</span><span className="text-[10px] uppercase tracking-wider text-cyan-300">{entity.type}</span></div><p className="mt-2 truncate text-[11px] text-slate-500">{entity.id}</p></div>)}
                        </div>
                        {!graph.entities.length && <p className="mt-6 text-sm text-slate-500">Index a repository to populate the knowledge graph.</p>}
                    </div>

                    <div className="border border-white/10 bg-white/[0.03] p-6">
                        <div className="flex items-center gap-3"><Sparkles className="h-5 w-5 text-amber-300" /><div><h2 className="font-semibold">RAG inspector</h2><p className="text-xs text-slate-500">Ask against indexed sources and inspect the evidence trail.</p></div></div>
                        <form onSubmit={ask} className="mt-6 flex gap-2"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask about repository evidence" className="min-w-0 flex-1 border border-white/10 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-cyan-300" /><button type="submit" title="Search indexed knowledge" className="bg-cyan-300 px-3 text-slate-950"><Search className="h-4 w-4" /></button></form>
                        {answer && <div className="mt-6 border-l-2 border-cyan-300 pl-4"><div className="flex items-center justify-between gap-3"><span className="text-xs uppercase tracking-wider text-cyan-300">{answer.provider}</span><span className="text-xs text-slate-500">Confidence {Math.round(answer.confidence * 100)}%</span></div><p className="mt-3 text-sm leading-6 text-slate-200">{answer.answer}</p><div className="mt-5 space-y-3">{answer.citations.map((citation) => <div key={`${citation.uri}-${citation.quote}`} className="text-xs text-slate-400"><p className="font-medium text-slate-300">{citation.title}</p><p className="mt-1 leading-5">&quot;{citation.quote}&quot;</p></div>)}</div></div>}
                        {!answer && <div className="mt-6 flex gap-3 border border-dashed border-white/10 p-4 text-sm text-slate-500"><CircleHelp className="h-4 w-4 shrink-0 text-slate-400" />Indexed sources and citations appear here after a query.</div>}
                    </div>
                </section>
                {error && <p className="mt-6 text-sm text-rose-300">{error}</p>}
            </div>
        </main>
    );
}
