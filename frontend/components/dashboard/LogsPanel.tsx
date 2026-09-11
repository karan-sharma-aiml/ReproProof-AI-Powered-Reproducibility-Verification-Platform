"use client";

import { Terminal } from "lucide-react";

export function LogsPanel({ lines }: { lines: string[] }) {
    return <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950"><div className="flex items-center gap-2 border-b border-slate-800 px-4 py-3 text-xs font-semibold text-slate-300"><Terminal className="h-4 w-4 text-brand-400" /> Execution logs <span className="ml-auto text-slate-500">live</span></div><div className="space-y-2 p-4 font-mono text-xs leading-5 text-slate-400">{lines.map((line, index) => <p key={`${line}-${index}`}><span className="mr-3 text-slate-600">{String(index + 1).padStart(2, "0")}</span>{line}</p>)}</div></div>;
}