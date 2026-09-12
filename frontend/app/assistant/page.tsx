"use client";

import { useState } from "react";
import { Bot, Copy, Send, Sparkles } from "lucide-react";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const prompts = ["Explain this repository", "Explain likely security findings", "Suggest dependency fixes", "Explain the Docker setup"];

export default function AssistantPage() {
    const [prompt, setPrompt] = useState("");
    const [answer, setAnswer] = useState("Ask RepoProof about the repository, dependencies, execution evidence, security, or Docker readiness.");
    const [meta, setMeta] = useState("Local gateway ready");
    const [loading, setLoading] = useState(false);

    async function ask(value = prompt) {
        if (!value.trim()) return;
        setLoading(true);
        try {
            const response = await fetch(`${apiBase}/providers/test?prompt=${encodeURIComponent(value)}`, { method: "POST" });
            const result = await response.json() as { content?: string; provider?: string; model?: string; fallback_used?: boolean };
            setAnswer(result.content ?? "The gateway returned no narrative response.");
            setMeta(`${result.provider ?? "local-mock"} · ${result.model ?? "mock-model"}${result.fallback_used ? " · offline fallback" : ""}`);
        } catch {
            setAnswer("The local assistant is offline. Start the backend to continue the evidence review.");
            setMeta("Gateway connection required");
        } finally { setLoading(false); }
    }

    return <main className="min-h-screen bg-slate-950 px-4 py-10 text-slate-100 sm:px-6 lg:px-10"><div className="mx-auto max-w-5xl"><header className="border-b border-white/10 pb-8"><p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300"><Sparkles className="h-4 w-4" /> AI assistant</p><h1 className="mt-3 text-4xl font-semibold tracking-tight">Ask RepoProof</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">Explain errors, generate patch ideas, review security and dependencies, or walk through the repository evidence.</p></header><section className="mt-8 grid gap-6 lg:grid-cols-[0.72fr_1.28fr]"><aside className="border border-white/10 bg-white/[0.03] p-5"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Suggested questions</p><div className="mt-4 space-y-2">{prompts.map((item) => <button key={item} type="button" onClick={() => { setPrompt(item); void ask(item); }} className="flex w-full items-center gap-3 border border-white/[0.07] px-3 py-3 text-left text-sm text-slate-300 hover:border-cyan-300/40 hover:bg-cyan-300/[0.06]"><Bot className="h-4 w-4 text-cyan-300" />{item}</button>)}</div></aside><section className="border border-cyan-300/20 bg-cyan-300/[0.04] p-6"><div className="flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">Gateway response</p><p className="mt-1 text-xs text-slate-500">{meta}</p></div><button type="button" onClick={() => void navigator.clipboard?.writeText(answer)} aria-label="Copy assistant response" className="rounded-lg p-2 text-slate-400 hover:bg-white/[0.06] hover:text-white"><Copy className="h-4 w-4" /></button></div><p className="mt-8 min-h-36 whitespace-pre-wrap text-lg leading-8 text-slate-200">{loading ? "Reviewing repository evidence..." : answer}</p><div className="mt-8 flex items-center gap-2 border-t border-white/10 pt-4"><input value={prompt} onChange={(event) => setPrompt(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void ask(); }} placeholder="Ask about your repository..." className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-600" /><button type="button" onClick={() => void ask()} disabled={loading || !prompt.trim()} aria-label="Send question" className="rounded-lg bg-cyan-400 p-2 text-slate-950 disabled:opacity-40"><Send className="h-4 w-4" /></button></div></section></section></div></main>;
}
