"use client";

import { useRef, useState } from "react";
import { ArrowRight, FileArchive, Github, LockKeyhole, UploadCloud } from "lucide-react";
import { GitHubRepoCard } from "@/components/cards/GitHubRepoCard";
import { RecentProjectsCard } from "@/components/cards/RecentProjectsCard";
import { VerificationStatusCard } from "@/components/cards/VerificationStatusCard";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { useStatus } from "@/hooks/useStatus";
import { useToast } from "@/hooks/useToast";
import { useUpload } from "@/hooks/useUpload";
import type { VerificationState } from "@/types";

export default function HomePage() {
    const inputRef = useRef<HTMLInputElement>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [repoUrl, setRepoUrl] = useState("");
    const [state, setState] = useState<VerificationState>("idle");
    const { upload, isUploading, progress, data, error } = useUpload();
    const { status, isLoading: statusLoading, refetch } = useStatus();
    const { addToast } = useToast();

    async function handleFile(file?: File) {
        if (!file) return;
        if (!file.name.toLowerCase().endsWith(".zip")) {
            addToast("error", "ZIP archive required", "Choose a .zip research artifact to continue.");
            return;
        }
        setState("uploading");
        const result = await upload(file);
        if (result) {
            setState("success");
            addToast("success", "Upload received", `${result.original_filename} is ready for verification.`);
            refetch();
        } else {
            setState("failed");
        }
    }

    function submitRepository(url: string) {
        setRepoUrl(url);
        addToast("info", "Repository queued", "GitHub verification will be available with the repository connector.");
    }

    return (
        <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-20">
            <section className="grid items-end gap-12 lg:grid-cols-[1.15fr_0.85fr]">
                <div>
                    <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-brand-700 dark:border-brand-800 dark:bg-brand-950/70 dark:text-brand-300">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" /> Research integrity infrastructure
                    </div>
                    <h1 className="max-w-3xl text-5xl font-bold tracking-tight text-slate-950 dark:text-white sm:text-7xl">
                        Make every result <span className="text-brand-600 dark:text-brand-400">reproducible.</span>
                    </h1>
                    <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-300">
                        ReproProof is an autonomous research reproducibility verification platform for teams that need evidence, not assurances.
                    </p>
                    <div className="mt-8 flex flex-wrap gap-5 text-sm text-slate-500 dark:text-slate-400">
                        <span className="inline-flex items-center gap-2"><LockKeyhole className="h-4 w-4 text-brand-500" /> Private by design</span>
                        <span className="inline-flex items-center gap-2"><FileArchive className="h-4 w-4 text-brand-500" /> ZIP artifacts up to 50 MB</span>
                    </div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/20">
                    <div className="mb-5 flex items-center justify-between">
                        <div><p className="text-sm font-semibold text-slate-950 dark:text-white">Start a verification</p><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Upload your experiment bundle to begin.</p></div>
                        <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-400">v1.0</span>
                    </div>
                    <button type="button" onClick={() => inputRef.current?.click()} onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }} onDragLeave={() => setIsDragging(false)} onDrop={(event) => { event.preventDefault(); setIsDragging(false); void handleFile(event.dataTransfer.files[0]); }} className={`flex min-h-56 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed transition ${isDragging ? "border-brand-500 bg-brand-50 dark:bg-brand-950/50" : "border-slate-300 bg-slate-50/70 hover:border-brand-400 hover:bg-brand-50/50 dark:border-slate-700 dark:bg-slate-950/40 dark:hover:border-brand-700"}`}>
                        {isUploading ? <><LoadingSpinner size="md" /><p className="mt-4 text-sm font-semibold text-slate-800 dark:text-slate-200">Uploading {progress}%</p><div className="mt-3 h-1.5 w-40 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div className="h-full bg-brand-500 transition-all" style={{ width: `${progress}%` }} /></div></> : <><UploadCloud className="h-9 w-9 text-brand-500" /><p className="mt-4 text-sm font-semibold text-slate-800 dark:text-slate-200">Drop a ZIP here or browse</p><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Research code, data, and environment files</p></>}
                    </button>
                    <input ref={inputRef} className="hidden" type="file" accept=".zip,application/zip" onChange={(event) => void handleFile(event.target.files?.[0])} />
                    {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
                    <div className="my-5 flex items-center gap-3 text-xs text-slate-400"><span className="h-px flex-1 bg-slate-200 dark:bg-slate-800" /> OR <span className="h-px flex-1 bg-slate-200 dark:bg-slate-800" /></div>
                    <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-950"><Github className="h-4 w-4 text-slate-400" /><input type="url" value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="GitHub repository URL" className="min-w-0 flex-1 border-0 bg-transparent text-sm outline-none placeholder:text-slate-400 focus:ring-0" /><button type="button" onClick={() => submitRepository(repoUrl)} disabled={!repoUrl} className="inline-flex items-center gap-1 text-sm font-semibold text-brand-600 disabled:opacity-40 dark:text-brand-400">Verify <ArrowRight className="h-4 w-4" /></button></div>
                </div>
            </section>
            <section className="mt-16 grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
                <RecentProjectsCard uploads={status?.uploads ?? []} isLoading={statusLoading} />
                <div className="space-y-6"><VerificationStatusCard state={state} filename={data?.original_filename} /><div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Platform status</p><div className="mt-4 flex items-center gap-3"><span className={`h-2.5 w-2.5 rounded-full ${status?.success ? "bg-emerald-500" : "bg-amber-500"}`} /><span className="text-sm font-medium text-slate-700 dark:text-slate-200">{status?.success ? "All systems operational" : "Checking backend connection"}</span></div></div></div>
            </section>
        </main>
    );
}