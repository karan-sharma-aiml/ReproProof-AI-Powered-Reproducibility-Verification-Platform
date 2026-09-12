"use client";

import type { LucideIcon } from "lucide-react";

interface StatCardProps {
    label: string;
    value: string;
    description?: string;
    icon: LucideIcon;
    tone?: "violet" | "green" | "amber" | "cyan";
    trend?: string;
}

const tones = {
    violet: "border-blue-400/20 bg-blue-400/[0.07] text-blue-300",
    green: "border-emerald-400/20 bg-emerald-400/[0.07] text-emerald-300",
    amber: "border-amber-400/20 bg-amber-400/[0.07] text-amber-300",
    cyan: "border-cyan-400/20 bg-cyan-400/[0.07] text-cyan-300",
};

export function StatCard({ label, value, description, icon: Icon, tone = "violet", trend }: StatCardProps) {
    return (
        <article className="group relative overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.045] p-5 shadow-[0_18px_50px_rgba(0,0,0,0.16)] backdrop-blur-xl transition duration-300 hover:-translate-y-1 hover:border-blue-300/30 hover:shadow-[0_22px_60px_rgba(2,132,199,0.16)]">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-blue-400/70 to-transparent opacity-0 transition group-hover:opacity-100" />
            <div className="flex items-start justify-between gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${tones[tone]}`}><Icon className="h-5 w-5" /></div>
                {trend && <span className="text-[11px] font-semibold text-emerald-300">{trend}</span>}
            </div>
            <p className="mt-5 text-xs font-medium uppercase tracking-[0.13em] text-[#94A3B8]">{label}</p>
            <p className="mt-1 text-3xl font-semibold tracking-tight text-[#F8FAFC]">{value}</p>
            {description && <p className="mt-2 text-xs text-[#94A3B8]">{description}</p>}
        </article>
    );
}
