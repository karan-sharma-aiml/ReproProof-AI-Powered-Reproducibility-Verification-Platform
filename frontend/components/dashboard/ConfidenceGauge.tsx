"use client";

import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";

export function ConfidenceGauge({ value, label = "Confidence" }: { value: number; label?: string }) {
    const normalizedValue = Math.max(0, Math.min(100, value));
    const rotation = (normalizedValue / 100) * 180 - 90;
    const color =
        normalizedValue >= 80
            ? "from-emerald-400 to-cyan-400"
            : normalizedValue >= 60
                ? "from-cyan-400 to-blue-400"
                : normalizedValue >= 40
                    ? "from-amber-400 to-orange-400"
                    : "from-rose-400 to-amber-400";

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.045] p-6"
        >
            {/* Gauge Container */}
            <div className="relative h-32 w-32">
                {/* Background Circle */}
                <svg className="h-full w-full" viewBox="0 0 120 120">
                    <defs>
                        <linearGradient id={`gauge-bg-${label}`} x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="rgba(255,255,255,0.1)" />
                            <stop offset="100%" stopColor="rgba(255,255,255,0.05)" />
                        </linearGradient>
                    </defs>
                    {/* Background Arc */}
                    <circle
                        cx="60"
                        cy="60"
                        r="50"
                        fill="none"
                        stroke={`url(#gauge-bg-${label})`}
                        strokeWidth="8"
                        strokeDasharray="157 314"
                        strokeLinecap="round"
                    />
                    {/* Progress Arc */}
                    <motion.circle
                        cx="60"
                        cy="60"
                        r="50"
                        fill="none"
                        stroke={`url(#gauge-fg-${label})`}
                        strokeWidth="8"
                        strokeDasharray={`${(normalizedValue / 100) * 157} 314`}
                        strokeLinecap="round"
                        animate={{ strokeDasharray: `${(normalizedValue / 100) * 157} 314` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                    />
                    <defs>
                        <linearGradient id={`gauge-fg-${label}`} x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#10b981" />
                            <stop offset="100%" stopColor="#06b6d4" />
                        </linearGradient>
                    </defs>
                </svg>

                {/* Center Content */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <motion.div
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="text-center"
                    >
                        <p className="text-3xl font-bold text-white">{normalizedValue}</p>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">%</p>
                    </motion.div>
                </div>
            </div>

            {/* Label and Status */}
            <div className="mt-4 text-center">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</p>
                <motion.p
                    animate={{
                        color:
                            normalizedValue >= 80
                                ? "#10b981"
                                : normalizedValue >= 60
                                    ? "#06b6d4"
                                    : normalizedValue >= 40
                                        ? "#f59e0b"
                                        : "#f43f5e",
                    }}
                    className="mt-2 text-sm font-semibold"
                >
                    {normalizedValue >= 80
                        ? "Excellent"
                        : normalizedValue >= 60
                            ? "Good"
                            : normalizedValue >= 40
                                ? "Fair"
                                : "Low"}
                </motion.p>
            </div>

            {/* Trend */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="mt-4 flex items-center gap-1.5 rounded-full bg-emerald-400/10 px-3 py-1.5 text-[10px] font-semibold text-emerald-300"
            >
                <TrendingUp className="h-3 w-3" />
                Trending up
            </motion.div>
        </motion.div>
    );
}
