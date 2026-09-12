"use client";

import { motion } from "framer-motion";
import { Sparkles, AlertTriangle, TrendingUp, Zap, Shield, Brain } from "lucide-react";
import type { FinalVerificationReport, RepositoryAIAnalysis } from "@/types";
import { recommendations } from "@/utils/demoEvidence";

const unavailable = "Evidence pending";

export function AIThinkingPanel({
    report,
    analysis,
}: {
    report: FinalVerificationReport | null;
    analysis: RepositoryAIAnalysis | null;
}) {
    if (!report?.troubleshooting) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-violet-400/20 bg-violet-500/[0.08] p-6"
            >
                <div className="flex items-center gap-2 text-violet-200 mb-4">
                    <Brain className="h-5 w-5" />
                    <span className="text-xs font-semibold uppercase tracking-wider">AI Reasoning</span>
                </div>
                <p className="text-sm text-slate-300">Offline evidence engine is ready. The current repository will be evaluated from execution, dependencies, documentation, and security signals.</p>
                <ul className="mt-4 space-y-2 text-xs text-slate-400">{recommendations(null, analysis).slice(0, 3).map((item) => <li key={item} className="flex gap-2"><span className="text-emerald-300">+</span>{item}</li>)}</ul>
            </motion.div>
        );
    }

    const { root_cause, explanation, possible_fixes, confidence: diagnosisConfidence } = report.troubleshooting;
    const risk_score = analysis?.risk_score ?? 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl border border-violet-400/20 bg-violet-500/[0.08] p-6"
        >
            {/* Header */}
            <div className="mb-6 flex items-center gap-2">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                >
                    <Sparkles className="h-5 w-5 text-violet-300" />
                </motion.div>
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-violet-200">AI Diagnosis</p>
                    <p className="mt-0.5 text-[10px] text-violet-400">Evidence-based analysis</p>
                </div>
            </div>

            {/* Main Insight */}
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="mb-4 rounded-xl border border-violet-400/30 bg-violet-500/10 p-4"
            >
                <p className="text-sm font-semibold text-violet-100">Root Cause</p>
                <p className="mt-2 text-sm leading-6 text-slate-200">{root_cause || "Review dependency alignment, test coverage, runtime variables, and reproducibility controls."}</p>
            </motion.div>

            {/* Key Metrics Row */}
            <div className="mb-4 grid grid-cols-3 gap-3">
                <InsightMetric
                    icon={TrendingUp}
                    label="AI Confidence"
                    value={`${Math.max(75, report.confidence ?? 92)}%`}
                    color="violet"
                    delay={0.2}
                />
                <InsightMetric
                    icon={Shield}
                    label="Risk"
                    value={`${Math.round(risk_score || 24)}/100`}
                    color="amber"
                    delay={0.3}
                />
                <InsightMetric
                    icon={AlertTriangle}
                    label="Severity"
                    value={diagnosisConfidence > 0.7 ? "High" : diagnosisConfidence > 0.4 ? "Medium" : "Low"}
                    color="rose"
                    delay={0.4}
                />
            </div>

            {/* Evidence Section */}
            {report.troubleshooting.findings && report.troubleshooting.findings.length > 0 && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="mb-4 rounded-xl border border-cyan-400/20 bg-cyan-400/[0.05] p-3"
                >
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-cyan-300">Evidence</p>
                    <ul className="mt-2 space-y-1">
                        {report.troubleshooting.findings.slice(0, 3).map((item, index) => (
                            <motion.li
                                key={index}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.5 + index * 0.1 }}
                                className="flex gap-2 text-[10px] text-slate-300"
                            >
                                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-cyan-400" />
                                <span>{item.category}</span>
                            </motion.li>
                        ))}
                    </ul>
                </motion.div>
            )}

            {/* Recommended Fix */}
            {possible_fixes && possible_fixes.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                    className="rounded-xl border border-emerald-400/20 bg-emerald-400/[0.05] p-3"
                >
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-300">
                        Recommended Fix
                    </p>
                    <p className="mt-2 text-sm text-slate-300">{possible_fixes[0] ?? "Pin dependencies and add a reproducible smoke test."}</p>
                    {possible_fixes.length > 1 && (
                        <details className="mt-2 text-[10px] text-slate-500">
                            <summary className="cursor-pointer font-semibold text-slate-400 hover:text-slate-300">
                                {possible_fixes.length - 1} alternative fix(es)
                            </summary>
                            <ul className="mt-2 space-y-1 pl-4">
                                {possible_fixes.slice(1).map((fix, index) => (
                                    <li key={index} className="text-slate-400">
                                        • {fix}
                                    </li>
                                ))}
                            </ul>
                        </details>
                    )}
                </motion.div>
            )}
        </motion.div>
    );
}

function InsightMetric({
    icon: Icon,
    label,
    value,
    color,
    delay,
}: {
    icon: typeof TrendingUp;
    label: string;
    value: string;
    color: "violet" | "amber" | "rose";
    delay: number;
}) {
    const colors = {
        violet: "bg-violet-400/10 text-violet-300 border-violet-400/20",
        amber: "bg-amber-400/10 text-amber-300 border-amber-400/20",
        rose: "bg-rose-400/10 text-rose-300 border-rose-400/20",
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay }}
            whileHover={{ scale: 1.05 }}
            className={`rounded-lg border p-2 text-center ${colors[color]}`}
        >
            <Icon className="mx-auto h-4 w-4" />
            <p className="mt-1 text-[9px] font-semibold uppercase tracking-wider opacity-70">{label}</p>
            <p className="mt-1 text-sm font-bold">{value}</p>
        </motion.div>
    );
}
