export function StatusChip({ label, tone = "neutral" }: { label: string; tone?: "success" | "warning" | "error" | "neutral" }) {
    const styles = {
        success: "border-emerald-400/20 bg-emerald-400/10 text-emerald-300",
        warning: "border-amber-400/20 bg-amber-400/10 text-amber-300",
        error: "border-rose-400/20 bg-rose-400/10 text-rose-300",
        neutral: "border-white/10 bg-white/[0.05] text-[#CBD5E1]",
    };
    return <span className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${styles[tone]}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{label}</span>;
}
