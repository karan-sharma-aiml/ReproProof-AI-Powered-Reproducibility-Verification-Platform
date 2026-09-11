"use client";

import { Check, Circle, Loader2, X } from "lucide-react";
import type { TimelineEntry } from "@/types";

export function ProgressTimeline({ entries }: { entries: TimelineEntry[] }) {
    return <ol className="space-y-5">{entries.map((entry) => { const Icon = entry.status === "done" ? Check : entry.status === "error" ? X : entry.status === "running" ? Loader2 : Circle; return <li key={entry.id} className="flex items-start gap-3"><span className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${entry.status === "done" ? "bg-emerald-100 text-emerald-600" : entry.status === "error" ? "bg-red-100 text-red-600" : entry.status === "running" ? "bg-brand-100 text-brand-600" : "bg-slate-100 text-slate-400"}`}><Icon className={`h-3.5 w-3.5 ${entry.status === "running" ? "animate-spin" : ""}`} /></span><div><p className="text-sm font-medium text-slate-800 dark:text-slate-200">{entry.label}</p>{entry.timestamp && <p className="mt-1 text-xs text-slate-400">{entry.timestamp}</p>}</div></li>; })}</ol>;
}