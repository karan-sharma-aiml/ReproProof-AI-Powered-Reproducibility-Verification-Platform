import type { ReactNode } from "react";

export function SectionCard({ title, eyebrow, action, children, className = "" }: { title: string; eyebrow?: string; action?: ReactNode; children: ReactNode; className?: string }) {
    return (
        <section className={`group relative overflow-hidden rounded-2xl border border-white/[0.09] bg-white/[0.045] p-5 shadow-[0_18px_50px_rgba(0,0,0,0.16)] backdrop-blur-xl ${className}`}>
            <div className="pointer-events-none absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-blue-400/70 to-transparent opacity-60" />
            <div className="mb-5 flex items-start justify-between gap-4">
                <div><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-blue-300/80">{eyebrow ?? "Workspace"}</p><h2 className="mt-1 text-base font-semibold tracking-tight text-[#F8FAFC]">{title}</h2></div>
                {action}
            </div>
            {children}
        </section>
    );
}
