import { Activity, Code2, Gauge, Languages, ShieldCheck } from "lucide-react";
import type { FinalVerificationReport, RepositoryMetadata, RepositoryAIAnalysis } from "@/types";
import { StatusChip } from "@/components/ui/StatusChip";

export function GlobalStatusBar({ repository, analysis, report, executionStatus = "Idle" }: { repository: RepositoryMetadata | null; analysis: RepositoryAIAnalysis | null; report: FinalVerificationReport | null; executionStatus?: string }) {
    const framework = repository?.detected_frameworks[0] ?? "Python project";
    const language = repository?.detected_languages[0] ?? "Language pending";
    const statusTone = executionStatus === "Completed" || executionStatus === "SUCCESS" ? "success" : executionStatus === "FAILED" ? "error" : executionStatus === "Running" ? "warning" : "neutral";
    return (
        <section className="mb-8 overflow-hidden rounded-2xl border border-violet-400/20 bg-[#101828] shadow-[0_20px_70px_rgba(34,24,84,0.22)]">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.07] bg-gradient-to-r from-violet-500/[0.12] via-transparent to-cyan-400/[0.06] px-5 py-4">
                <div className="flex min-w-0 items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/15 text-violet-300"><ShieldCheck className="h-5 w-5" /></div><div className="min-w-0"><p className="truncate text-sm font-semibold text-[#F8FAFC]">{repository?.repository_name ?? "No repository selected"}</p><p className="text-xs text-[#94A3B8]">Reproducibility control plane</p></div></div>
                <StatusChip label={executionStatus} tone={statusTone} />
            </div>
            <div className="grid gap-4 px-5 py-4 sm:grid-cols-2 lg:grid-cols-5">
                <StatusItem icon={Code2} label="Framework" value={framework} /><StatusItem icon={Languages} label="Language" value={language} /><StatusItem icon={Activity} label="Stage" value={executionStatus === "Idle" ? "Awaiting run" : executionStatus} /><StatusItem icon={Gauge} label="Health" value={`${repository?.health_score ?? 0}/100`} /><StatusItem icon={ShieldCheck} label="AI Confidence" value={`${report?.confidence ?? 0}%`} />
            </div>
        </section>
    );
}

function StatusItem({ icon: Icon, label, value }: { icon: typeof Activity; label: string; value: string }) { return <div className="min-w-0"><p className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-[#64748B]"><Icon className="h-3.5 w-3.5 text-violet-300" />{label}</p><p className="mt-2 truncate text-sm font-medium text-[#E2E8F0]">{value}</p></div>; }
