"use client";

import Link from "next/link";
import { Bot } from "lucide-react";

export function FloatingAssistant() {
    return <Link href="/assistant" aria-label="Open AI Assistant" title="Ask RepoProof" className="fixed bottom-5 right-5 z-50 inline-flex items-center gap-2 rounded-full border border-cyan-300/30 bg-slate-950/95 px-4 py-3 text-xs font-semibold text-cyan-200 shadow-2xl shadow-cyan-950/40 backdrop-blur transition hover:-translate-y-1 hover:border-cyan-200/70"><Bot className="h-4 w-4" /> Ask RepoProof</Link>;
}
