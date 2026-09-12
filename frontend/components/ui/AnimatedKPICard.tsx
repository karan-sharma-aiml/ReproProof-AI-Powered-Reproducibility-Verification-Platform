"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import type { LucideIcon } from "lucide-react";

interface AnimatedKPICardProps {
    icon: LucideIcon;
    label: string;
    value: string | number;
    trend?: string;
    trendDirection?: "up" | "down" | "neutral";
    description?: string;
    tone?: "violet" | "cyan" | "green" | "amber";
}

export function AnimatedKPICard({
    icon: Icon,
    label,
    value,
    trend,
    trendDirection = "neutral",
    description,
    tone = "violet",
}: AnimatedKPICardProps) {
    const [displayValue, setDisplayValue] = useState(0);
    const numericValue = typeof value === "number" ? value : parseInt(String(value), 10);
    const isNumeric = !isNaN(numericValue);

    // Animate number counter
    useEffect(() => {
        if (!isNumeric) return;

        let start = 0;
        const end = numericValue;
        const duration = 1000; // ms
        const increment = end / (duration / 16); // 16ms per frame (~60fps)

        const timer = setInterval(() => {
            start += increment;
            if (start >= end) {
                setDisplayValue(end);
                clearInterval(timer);
            } else {
                setDisplayValue(Math.floor(start));
            }
        }, 16);

        return () => clearInterval(timer);
    }, [numericValue, isNumeric]);

    const toneColors = {
        violet: {
            bg: "bg-violet-400/10",
            border: "border-violet-400/20",
            text: "text-violet-400",
            icon: "text-violet-300",
        },
        cyan: {
            bg: "bg-cyan-400/10",
            border: "border-cyan-400/20",
            text: "text-cyan-400",
            icon: "text-cyan-300",
        },
        green: {
            bg: "bg-emerald-400/10",
            border: "border-emerald-400/20",
            text: "text-emerald-400",
            icon: "text-emerald-300",
        },
        amber: {
            bg: "bg-amber-400/10",
            border: "border-amber-400/20",
            text: "text-amber-400",
            icon: "text-amber-300",
        },
    };

    const colors = toneColors[tone];

    return (
        <motion.article
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -4, scale: 1.02 }}
            className={`rounded-2xl border ${colors.border} ${colors.bg} p-5 transition-all duration-300 cursor-pointer hover:shadow-lg hover:shadow-${tone}-500/20`}
        >
            {/* Icon */}
            <motion.div
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 4, repeat: Infinity }}
                className={`h-10 w-10 rounded-lg ${colors.bg} flex items-center justify-center`}
            >
                <Icon className={`h-5 w-5 ${colors.icon}`} />
            </motion.div>

            {/* Label */}
            <p className="mt-4 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p>

            {/* Value with animation */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="mt-1"
            >
                <motion.p className={`text-2xl font-bold ${colors.text}`}>
                    {isNumeric ? displayValue : value}
                </motion.p>
            </motion.div>

            {/* Description */}
            {description && (
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="mt-2 text-xs text-slate-500"
                >
                    {description}
                </motion.p>
            )}

            {/* Trend */}
            {trend && (
                <motion.div
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className={`mt-3 flex items-center gap-1.5 text-xs font-semibold ${trendDirection === "up"
                            ? "text-emerald-400"
                            : trendDirection === "down"
                                ? "text-rose-400"
                                : "text-slate-400"
                        }`}
                >
                    <motion.span
                        animate={{ y: trendDirection === "up" ? [-2, 0, -2] : trendDirection === "down" ? [2, 0, 2] : 0 }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                    >
                        {trendDirection === "up" ? "↑" : trendDirection === "down" ? "↓" : "→"}
                    </motion.span>
                    {trend}
                </motion.div>
            )}

            {/* Gradient Border Animation */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="absolute inset-0 rounded-2xl pointer-events-none"
                style={{
                    background: `linear-gradient(45deg, ${tone === "violet" ? "rgba(167, 139, 250, 0.1)" : tone === "cyan" ? "rgba(34, 211, 238, 0.1)" : tone === "green" ? "rgba(52, 211, 153, 0.1)" : "rgba(251, 146, 60, 0.1)"}, transparent)`,
                }}
            />
        </motion.article>
    );
}

export function AnimatedKPIGrid({
    kpis,
}: {
    kpis: (Omit<AnimatedKPICardProps, "icon"> & { icon: LucideIcon })[];
}) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
            {kpis.map((kpi, index) => (
                <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                >
                    <AnimatedKPICard {...kpi} />
                </motion.div>
            ))}
        </motion.div>
    );
}
