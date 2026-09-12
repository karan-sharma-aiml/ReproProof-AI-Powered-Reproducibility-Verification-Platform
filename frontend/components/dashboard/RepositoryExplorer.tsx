"use client";

import { motion } from "framer-motion";
import {
    Code2, Database, FileCode2, GitBranch, Package, Shield, AlertCircle, TrendingUp, CheckCircle2, Gauge,
    BarChart3, Users, Calendar, Lock, Eye, FileText,
} from "lucide-react";
import type { RepositoryMetadata, RepositoryAIAnalysis } from "@/types";

const unavailable = "Not Available";

export function RepositoryExplorer({
    repository,
    analysis,
    loading,
}: {
    repository: RepositoryMetadata | null;
    analysis: RepositoryAIAnalysis | null;
    loading: boolean;
}) {
    if (!repository) {
        return (
            <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-8 text-center">
                <p className="text-sm text-slate-400">No repository data available</p>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl border border-white/10 bg-white/[0.045] p-6"
        >
            {/* Header */}
            <div className="mb-6 flex items-start justify-between">
                <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Repository</p>
                    <h3 className="mt-1 text-xl font-semibold text-white">{repository.repository_name}</h3>
                </div>
                <motion.div
                    whileHover={{ scale: 1.05 }}
                    className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1.5"
                >
                    <span className="text-xs font-semibold text-emerald-300">● Public</span>
                </motion.div>
            </div>

            {/* Key Metrics Grid */}
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <MetricBox
                    icon={Code2}
                    label="Language"
                    value={repository.detected_languages[0] || unavailable}
                    color="blue"
                />
                <MetricBox
                    icon={Package}
                    label="Framework"
                    value={repository.detected_frameworks[0] || unavailable}
                    color="green"
                />
                <MetricBox
                    icon={FileCode2}
                    label="Files"
                    value={String(repository.total_files)}
                    color="violet"
                />
                <MetricBox
                    icon={Database}
                    label="Datasets"
                    value={String(repository.datasets.length)}
                    color="cyan"
                />
            </div>

            {/* Details Grid */}
            <div className="mb-6 grid gap-4 sm:grid-cols-2">
                <DetailCard
                    icon={Gauge}
                    label="Health Score"
                    value={`${repository.health_score}/100`}
                    description="Repository structural readiness"
                />
                <DetailCard
                    icon={Shield}
                    label="Security Status"
                    value={analysis?.risk_score ? `${analysis.risk_score}/100 risk` : unavailable}
                    description="Vulnerability assessment"
                />
                <DetailCard
                    icon={TrendingUp}
                    label="Execution Count"
                    value="1"
                    description="Captured runs in this session"
                />
                <DetailCard
                    icon={CheckCircle2}
                    label="Tests"
                    value={repository.important_files.some((f) => /test|spec/.test(f)) ? "Detected" : "None found"}
                    description="Test suite presence"
                />
            </div>

            {/* Features Row */}
            <div className="grid gap-2 sm:grid-cols-3 border-t border-white/10 pt-4">
                <FeatureBox
                    icon={FileText}
                    label="README"
                    value={repository.important_files.some((f) => /readme/i.test(f)) ? "✓" : "✗"}
                />
                <FeatureBox
                    icon={Lock}
                    label="License"
                    value={repository.important_files.some((f) => /license|copying/i.test(f)) ? "✓" : "✗"}
                />
                <FeatureBox
                    icon={FileText}
                    label="Docker"
                    value={repository.important_files.some((f) => /docker/i.test(f)) ? "✓" : "✗"}
                />
            </div>

            {/* Dependency Manifests */}
            {repository.important_files.some((f) => /requirements|pyproject|setup|environment/.test(f)) && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-4 rounded-xl border border-cyan-400/20 bg-cyan-400/[0.05] p-3"
                >
                    <p className="text-xs font-semibold text-cyan-300">
                        📦 {repository.important_files.filter((f) => /requirements|pyproject|setup|environment/.test(f)).length}{" "}
                        dependency manifest(s) detected
                    </p>
                </motion.div>
            )}
        </motion.div>
    );
}

function MetricBox({
    icon: Icon,
    label,
    value,
    color,
}: {
    icon: typeof Code2;
    label: string;
    value: string;
    color: "blue" | "green" | "violet" | "cyan";
}) {
    const colors = {
        blue: "bg-blue-400/10 text-blue-300 border-blue-400/20",
        green: "bg-emerald-400/10 text-emerald-300 border-emerald-400/20",
        violet: "bg-violet-400/10 text-violet-300 border-violet-400/20",
        cyan: "bg-cyan-400/10 text-cyan-300 border-cyan-400/20",
    };

    return (
        <motion.div
            whileHover={{ scale: 1.05, y: -2 }}
            className={`rounded-xl border p-3 text-center transition ${colors[color]}`}
        >
            <Icon className="mx-auto h-4 w-4" />
            <p className="mt-2 text-[10px] font-semibold uppercase tracking-wider opacity-70">{label}</p>
            <p className="mt-1 truncate text-sm font-semibold">{value}</p>
        </motion.div>
    );
}

function DetailCard({
    icon: Icon,
    label,
    value,
    description,
}: {
    icon: typeof Gauge;
    label: string;
    value: string;
    description: string;
}) {
    return (
        <motion.div
            whileHover={{ y: -2 }}
            className="rounded-xl border border-white/[0.07] bg-white/[0.03] p-3"
        >
            <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-violet-400/10 text-violet-300">
                    <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-600">{label}</p>
                    <p className="mt-1 text-sm font-semibold text-slate-200">{value}</p>
                    <p className="mt-0.5 text-[10px] text-slate-600">{description}</p>
                </div>
            </div>
        </motion.div>
    );
}

function FeatureBox({
    icon: Icon,
    label,
    value,
}: {
    icon: typeof FileText;
    label: string;
    value: string;
}) {
    const isPresent = value === "✓";

    return (
        <motion.div
            whileHover={{ scale: 1.02 }}
            className={`rounded-lg border px-3 py-2 text-center ${isPresent ? "border-emerald-400/20 bg-emerald-400/[0.05]" : "border-slate-400/10 bg-slate-400/[0.03]"
                }`}
        >
            <Icon className={`mx-auto h-4 w-4 ${isPresent ? "text-emerald-400" : "text-slate-500"}`} />
            <p className="mt-1 text-[10px] font-semibold text-slate-300">{label}</p>
            <motion.p
                animate={{ scale: isPresent ? 1.2 : 1 }}
                className={`mt-1 text-base font-bold ${isPresent ? "text-emerald-400" : "text-slate-600"}`}
            >
                {value}
            </motion.p>
        </motion.div>
    );
}
