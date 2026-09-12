"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, FileArchive, Github, LockKeyhole, UploadCloud } from "lucide-react";
import { GitHubRepoCard } from "@/components/cards/GitHubRepoCard";
import { RecentProjectsCard } from "@/components/cards/RecentProjectsCard";
import { VerificationStatusCard } from "@/components/cards/VerificationStatusCard";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { GlassCard, StatusBadge } from "@/components/ui/EnterprisePrimitives";
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
    const router = useRouter();

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
            router.push("/dashboard");
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
                    <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-400/30 bg-violet-400/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-violet-300">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" /> Research integrity infrastructure
                    </div>
                    <h1 className="max-w-3xl text-5xl font-semibold tracking-[-0.03em] text-white sm:text-7xl">
                        Make every result <span className="text-violet-400">reproducible.</span>
                    </h1>
                    <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-300">
                        ReproProof is an autonomous research reproducibility verification platform for teams that need evidence, not assurances.
                    </p>
                    <div className="mt-8 flex flex-wrap gap-5 text-sm text-slate-400">
                        <span className="inline-flex items-center gap-2"><LockKeyhole className="h-4 w-4 text-violet-400" /> Private by design</span>
                        <span className="inline-flex items-center gap-2"><FileArchive className="h-4 w-4 text-violet-400" /> ZIP artifacts up to 50 MB</span>
                    </div>
                </div>
                <GlassCard className="border-violet-400/20 bg-[#101828]/95 p-6 shadow-[0_24px_80px_rgba(38,24,91,0.3)]">
                    <div className="mb-5 flex items-center justify-between">
                        <div><p className="text-sm font-semibold text-white">Start a verification</p><p className="mt-1 text-xs text-slate-400">Upload your experiment bundle to begin.</p></div>
                        <span className="rounded-lg bg-white/10 px-2.5 py-1 text-xs font-medium text-slate-300">v1.0</span>
                    </div>
                    <button type="button" onClick={() => inputRef.current?.click()} onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }} onDragLeave={() => setIsDragging(false)} onDrop={(event) => { event.preventDefault(); setIsDragging(false); void handleFile(event.dataTransfer.files[0]); }} className={`flex min-h-56 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed transition ${isDragging ? "border-violet-400 bg-violet-500/10" : "border-white/10 bg-[#151F32] hover:border-violet-400/60 hover:bg-violet-500/[0.08]"}`}>
                        {isUploading ? <><LoadingSpinner size="md" /><p className="mt-4 text-sm font-semibold text-slate-200">Uploading {progress}%</p><div className="mt-3 h-1.5 w-40 overflow-hidden rounded-full bg-white/10"><div className="h-full bg-violet-400 transition-all" style={{ width: `${progress}%` }} /></div></> : <><UploadCloud className="h-9 w-9 text-violet-400" /><p className="mt-4 text-sm font-semibold text-slate-200">Drop a ZIP here or browse</p><p className="mt-1 text-xs text-slate-400">Research code, data, and environment files</p></>}
                    </button>
                    <input ref={inputRef} className="hidden" type="file" accept=".zip,application/zip" onChange={(event) => void handleFile(event.target.files?.[0])} />
                    {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
                    <div className="my-5 flex items-center gap-3 text-xs text-slate-400"><span className="h-px flex-1 bg-white/10" /> OR <span className="h-px flex-1 bg-white/10" /></div>
                    <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2"><Github className="h-4 w-4 text-slate-400" /><input type="url" value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="GitHub repository URL" className="min-w-0 flex-1 border-0 bg-transparent text-sm outline-none placeholder:text-slate-500 focus:ring-0" /><button type="button" onClick={() => submitRepository(repoUrl)} disabled={!repoUrl} className="inline-flex items-center gap-1 text-sm font-semibold text-violet-400 disabled:opacity-40">Verify <ArrowRight className="h-4 w-4" /></button></div>
                </GlassCard>
            </section>
            <section className="mt-16 grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
                <RecentProjectsCard uploads={status?.uploads ?? []} isLoading={statusLoading} />
                <div className="space-y-6"><VerificationStatusCard state={state} filename={data?.original_filename} /><GlassCard><p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Platform status</p><div className="mt-4 flex items-center gap-3"><StatusBadge label={status?.success ? "Systems operational" : "Checking connection"} tone={status?.success ? "success" : "warning"} /></div></GlassCard></div>
            </section>
        </main>
    );
}