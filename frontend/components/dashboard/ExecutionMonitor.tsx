"use client";

import { Play, Terminal } from "lucide-react";
import type { ExecutionEvent } from "@/types";

interface ExecutionMonitorProps {
    repositoryId?: string;
    events: ExecutionEvent[];
    status: string;
    currentStage: string;
    progress: number;
    elapsedSeconds: number;
    isRunning: boolean;
    onStart: () => void;
}

export function ExecutionMonitor({ repositoryId, events, status, currentStage, progress, elapsedSeconds, isRunning, onStart }: ExecutionMonitorProps) {
    const stdout = events.filter((event) => event.stream === "stdout");
    const stderr = events.filter((event) => event.stream === "stderr");
    return <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Live execution</p><h2 className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">Execution monitor</h2></div><div className="flex items-center gap-3"><span className={`rounded-full px-2.5 py-1 text-xs font-bold ${status === "SUCCESS" || status === "COMPLETED" ? "bg-emerald-100 text-emerald-700" : status === "FAILED" || status === "TIMEOUT" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>{status}</span><span className="font-mono text-xs text-slate-500">00:{String(elapsedSeconds).padStart(2, "0")}</span>{repositoryId && <button type="button" onClick={onStart} disabled={isRunning} className="inline-flex items-center gap-1 rounded-lg bg-brand-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"><Play className="h-3.5 w-3.5" /> {isRunning ? "Running" : "Run"}</button>}</div></div><div className="mt-4"><div className="flex justify-between text-xs text-slate-500"><span>{currentStage}</span><span>{progress}%</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700"><div className="h-full bg-brand-500 transition-all" style={{ width: `${progress}%` }} /></div></div><div className="mt-5 grid gap-4 md:grid-cols-2"><TerminalPanel title="stdout" lines={stdout} /><TerminalPanel title="stderr" lines={stderr} error /></div></section>;
}

function TerminalPanel({ title, lines, error = false }: { title: string; lines: ExecutionEvent[]; error?: boolean }) { return <div className="overflow-hidden rounded-lg bg-slate-950"><div className="flex items-center gap-2 border-b border-slate-800 px-3 py-2 text-xs font-semibold text-slate-400"><Terminal className="h-3.5 w-3.5" /> {title}</div><div className={`h-32 overflow-auto p-3 font-mono text-xs leading-5 ${error ? "text-red-300" : "text-emerald-300"}`}>{lines.length ? lines.map((line, index) => <div key={`${line.timestamp}-${index}`}>&gt; {line.message}</div>) : <span className="text-slate-600">Waiting for output...</span>}</div></div>; }