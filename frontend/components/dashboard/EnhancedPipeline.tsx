"use client";

import { motion } from "framer-motion";
import {
    Upload, Package, Wrench, Zap, Sparkles, GitPullRequest, CheckCircle2, XCircle, AlertCircle, Clock3, TrendingUp,
} from "lucide-react";
import type { ExecutionEvent, FinalVerificationReport } from "@/types";

const pipeline = [
    { name: "Upload", icon: Upload, stage: "REPOSITORY_UPLOADED", description: "Artifact received" },
    { name: "Analysis", icon: Package, stage: "REPOSITORY_ANALYSIS_COMPLETE", description: "Scanning repository" },
    { name: "Dependencies", icon: Wrench, stage: "DEPENDENCY_DETECTION", description: "Dependency scan" },
    { name: "Sandbox", icon: AlertCircle, stage: "SANDBOX_CREATED", description: "Build environment" },
    { name: "Execution", icon: Zap, stage: "EXECUTION_STARTED", description: "Running tests" },
    { name: "AI Diagnosis", icon: Sparkles, stage: "AI_ANALYSIS", description: "Root cause analysis" },
    { name: "Patch", icon: GitPullRequest, stage: "PATCH_GENERATED", description: "Generating fix" },
    { name: "Self-Heal", icon: Wrench, stage: "RERUN", description: "Applying solution" },
    { name: "Verification", icon: CheckCircle2, stage: "VERIFICATION_READY", description: "Final validation" },
] as const;

export function EnhancedPipeline({
    events,
    report,
    currentStage,
}: {
    events: ExecutionEvent[];
    report: FinalVerificationReport | null;
    currentStage: string;
}) {
    return (
        <div className="overflow-x-auto pb-4">
            <div className="flex min-w-max items-start gap-2 px-2">
                {pipeline.map((stage, index) => {
                    const event = events.find((item) => item.stage === stage.stage);
                    const complete = Boolean(event?.status === "SUCCESS" || (stage.stage === "VERIFICATION_READY" && report));
                    const running = currentStage === stage.stage || event?.status === "RUNNING";
                    const failed = event?.status === "FAILED";
                    const Icon = stage.icon;

                    return (
                        <motion.div
                            key={stage.stage}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="flex flex-col items-center"
                        >
                            {/* Stage Circle */}
                            <motion.div
                                whileHover={{ scale: 1.1 }}
                                className={`relative flex h-14 w-14 items-center justify-center rounded-full border-2 transition-all cursor-pointer group ${complete
                                        ? "border-emerald-400/50 bg-emerald-400/10 text-emerald-300 shadow-lg shadow-emerald-500/20"
                                        : failed
                                            ? "border-rose-400/50 bg-rose-400/10 text-rose-300 shadow-lg shadow-rose-500/10"
                                            : running
                                                ? "border-violet-400/80 bg-violet-500/20 text-violet-200 shadow-xl shadow-violet-500/30 animate-pulse"
                                                : "border-white/10 bg-white/[0.04] text-slate-600"
                                    }`}
                            >
                                <Icon className="h-5 w-5" />

                                {/* Tooltip */}
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }}
                                    whileHover={{ opacity: 1, y: -40 }}
                                    className="absolute left-1/2 top-full mt-2 -translate-x-1/2 pointer-events-none group-hover:pointer-events-auto"
                                >
                                    <div className="rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-center whitespace-nowrap text-xs text-slate-300 shadow-xl">
                                        <p className="font-semibold">{stage.name}</p>
                                        <p className="text-[10px] text-slate-500">{stage.description}</p>
                                        {event?.message && (
                                            <p className="mt-1 text-[10px] text-emerald-400">
                                                ✓ {event.message}
                                            </p>
                                        )}
                                    </div>
                                </motion.div>
                            </motion.div>

                            {/* Stage Label */}
                            <p className="mt-3 text-xs font-semibold text-slate-300 text-center">{stage.name}</p>

                            {/* Status Label */}
                            <motion.p
                                animate={{
                                    color: complete ? "#10b981" : failed ? "#f43f5e" : running ? "#a78bfa" : "#64748b",
                                }}
                                className="mt-1 text-[10px] font-semibold uppercase tracking-wider"
                            >
                                {complete ? "✓" : failed ? "✗" : running ? "●" : "○"}
                            </motion.p>

                            {/* Duration (if available) */}
                            {/* Duration not available on ExecutionEvent */}

                            {/* Confidence Score (if available) */}
                            {/* Confidence not available on ExecutionEvent */}
                        </motion.div>
                    );
                })}
            </div>

            {/* Progress Summary */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="mt-6 rounded-xl border border-white/10 bg-white/[0.04] p-3"
            >
                <div className="grid grid-cols-4 gap-2 text-center">
                    <Stat
                        label="Completed"
                        value={events.filter((e) => e.status === "SUCCESS").length}
                        color="emerald"
                    />
                    <Stat label="Running" value={events.filter((e) => e.status === "RUNNING").length} color="violet" />
                    <Stat label="Failed" value={events.filter((e) => e.status === "FAILED").length} color="rose" />
                    <Stat
                        label="Pending"
                        value={pipeline.length - events.filter((e) => e.status === "SUCCESS" || e.status === "FAILED").length}
                        color="slate"
                    />
                </div>
            </motion.div>
        </div>
    );
}

function Stat({
    label,
    value,
    color,
}: {
    label: string;
    value: number;
    color: "emerald" | "violet" | "rose" | "slate";
}) {
    const colors = {
        emerald: "text-emerald-400 bg-emerald-400/10",
        violet: "text-violet-400 bg-violet-400/10",
        rose: "text-rose-400 bg-rose-400/10",
        slate: "text-slate-400 bg-slate-400/10",
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-lg ${colors[color]} py-2`}
        >
            <motion.p className="text-lg font-bold">{value}</motion.p>
            <p className="text-[10px] font-semibold uppercase tracking-wider opacity-70">{label}</p>
        </motion.div>
    );
}
