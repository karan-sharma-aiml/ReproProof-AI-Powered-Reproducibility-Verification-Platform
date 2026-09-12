"use client";

import { motion } from "framer-motion";

const shimmer = {
    initial: { backgroundPosition: "0% 0%" },
    animate: { backgroundPosition: "100% 100%" },
};

export function LoadingSkeleton({ className = "h-12 w-full" }: { className?: string }) {
    return (
        <motion.div
            variants={shimmer}
            initial="initial"
            animate="animate"
            transition={{ duration: 2, repeat: Infinity }}
            className={`rounded-xl bg-gradient-to-r from-white/[0.03] via-white/[0.08] to-white/[0.03] ${className}`}
            style={{
                backgroundSize: "200% 100%",
            }}
        />
    );
}

export function SkeletonCard() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-2xl border border-white/10 bg-white/[0.045] p-5"
        >
            <LoadingSkeleton className="h-4 w-24" />
            <LoadingSkeleton className="mt-3 h-6 w-32" />
            <div className="mt-4 space-y-2">
                <LoadingSkeleton className="h-3 w-full" />
                <LoadingSkeleton className="h-3 w-4/5" />
                <LoadingSkeleton className="h-3 w-3/4" />
            </div>
        </motion.div>
    );
}

export function SkeletonMetricCard() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-2xl border border-white/[0.08] bg-[#101828] p-5"
        >
            <LoadingSkeleton className="h-5 w-5 rounded-lg" />
            <LoadingSkeleton className="mt-4 h-3 w-20" />
            <LoadingSkeleton className="mt-2 h-8 w-16" />
        </motion.div>
    );
}

export function SkeletonPipeline() {
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-2">
            {Array.from({ length: 9 }).map((_, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex flex-col items-center gap-2"
                >
                    <LoadingSkeleton className="h-14 w-14 rounded-full" />
                    <LoadingSkeleton className="h-2 w-12" />
                </motion.div>
            ))}
        </motion.div>
    );
}

export function SkeletonTimeline() {
    return (
        <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex gap-3"
                >
                    <LoadingSkeleton className="h-2 w-2 rounded-full" />
                    <div className="flex-1 space-y-2">
                        <LoadingSkeleton className="h-3 w-24" />
                        <LoadingSkeleton className="h-2 w-32" />
                    </div>
                </motion.div>
            ))}
        </div>
    );
}

export function SkeletonActivityFeed() {
    return (
        <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex gap-3 rounded-xl border border-white/[0.06] bg-white/[0.025] p-3"
                >
                    <LoadingSkeleton className="h-8 w-8 rounded-lg" />
                    <div className="flex-1 space-y-1">
                        <LoadingSkeleton className="h-3 w-24" />
                        <LoadingSkeleton className="h-2 w-32" />
                    </div>
                </motion.div>
            ))}
        </div>
    );
}

export function SkeletonRepositoryExplorer() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-2xl border border-white/10 bg-white/[0.045] p-6"
        >
            <div className="mb-6 flex items-start justify-between">
                <div className="flex-1">
                    <LoadingSkeleton className="h-3 w-24" />
                    <LoadingSkeleton className="mt-2 h-6 w-32" />
                </div>
                <LoadingSkeleton className="h-8 w-20 rounded-full" />
            </div>

            <div className="mb-6 grid grid-cols-4 gap-3">
                {Array.from({ length: 4 }).map((_, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.05 }}
                    >
                        <LoadingSkeleton className="h-20 w-full rounded-xl" />
                    </motion.div>
                ))}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
                {Array.from({ length: 4 }).map((_, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.05 }}
                        className="space-y-2 rounded-xl border border-white/[0.07] bg-white/[0.03] p-3"
                    >
                        <LoadingSkeleton className="h-3 w-20" />
                        <LoadingSkeleton className="h-4 w-24" />
                    </motion.div>
                ))}
            </div>
        </motion.div>
    );
}
