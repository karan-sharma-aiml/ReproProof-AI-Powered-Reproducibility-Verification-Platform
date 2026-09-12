"use client";

import { motion } from "framer-motion";
import { Copy, Download, Search, Filter, ChevronDown } from "lucide-react";
import { useState, useRef } from "react";

export function TerminalExecutionLogs({ content = "" }: { content?: string }) {
    const [searchTerm, setSearchTerm] = useState("");
    const [showFilters, setShowFilters] = useState(false);
    const [filterLevel, setFilterLevel] = useState<"all" | "error" | "warning" | "info">("all");
    const [copied, setCopied] = useState(false);
    const contentRef = useRef<HTMLPreElement>(null);

    const lines = content.split("\n");
    const filteredLines = lines.filter((line) => {
        const matchesSearch = line.toLowerCase().includes(searchTerm.toLowerCase());
        if (filterLevel === "all") return matchesSearch;
        if (filterLevel === "error") return matchesSearch && (line.includes("ERROR") || line.includes("error"));
        if (filterLevel === "warning") return matchesSearch && (line.includes("WARN") || line.includes("warn"));
        if (filterLevel === "info") return matchesSearch && (line.includes("INFO") || line.includes("info"));
        return matchesSearch;
    });

    const handleCopy = async () => {
        if (contentRef.current && navigator.clipboard) {
            await navigator.clipboard.writeText(contentRef.current.innerText);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleDownload = () => {
        const blob = new Blob([content], { type: "text/plain" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "execution-logs.txt";
        a.click();
        window.URL.revokeObjectURL(url);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col rounded-2xl border border-white/10 bg-slate-950 overflow-hidden"
        >
            {/* Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 bg-slate-900/50 px-4 py-3">
                <div className="flex flex-1 items-center gap-2 min-w-0">
                    <div className="relative flex-1 max-w-xs">
                        <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Search logs..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full rounded-lg border border-white/10 bg-white/[0.04] py-1.5 pl-8 pr-3 text-xs text-slate-200 placeholder:text-slate-600 focus:border-violet-400/40 focus:outline-none"
                        />
                    </div>
                </div>

                <div className="flex items-center gap-1.5">
                    {/* Filter */}
                    <div className="relative">
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            type="button"
                            aria-label="Filter execution logs"
                            onClick={() => setShowFilters(!showFilters)}
                            className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/[0.08]"
                        >
                            <Filter className="h-3.5 w-3.5" />
                            <ChevronDown className="h-3 w-3" />
                        </motion.button>
                        {showFilters && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="absolute right-0 top-full mt-1 rounded-lg border border-white/10 bg-slate-900 py-1 shadow-xl z-10"
                            >
                                {(["all", "error", "warning", "info"] as const).map((level) => (
                                    <button
                                        type="button"
                                        key={level}
                                        onClick={() => {
                                            setFilterLevel(level);
                                            setShowFilters(false);
                                        }}
                                        className={`block w-full px-4 py-1.5 text-left text-xs font-medium transition ${filterLevel === level
                                            ? "bg-violet-500/20 text-violet-300"
                                            : "text-slate-400 hover:bg-white/[0.05]"
                                            }`}
                                    >
                                        {level.charAt(0).toUpperCase() + level.slice(1)}
                                    </button>
                                ))}
                            </motion.div>
                        )}
                    </div>

                    {/* Copy Button */}
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        type="button"
                        aria-label="Copy execution logs"
                        onClick={() => void handleCopy()}
                        className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/[0.08]"
                    >
                        <Copy className="h-3.5 w-3.5" />
                        {copied ? "Copied" : "Copy"}
                    </motion.button>

                    {/* Download Button */}
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        type="button"
                        aria-label="Export execution logs"
                        onClick={handleDownload}
                        className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/[0.08]"
                    >
                        <Download className="h-3.5 w-3.5" />
                        Export
                    </motion.button>
                </div>
            </div>

            {/* Content */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="max-h-96 overflow-auto flex-1"
            >
                <pre
                    ref={contentRef}
                    className="p-4 font-mono text-xs leading-6 text-slate-300"
                    style={{
                        whiteSpace: "pre-wrap",
                        wordWrap: "break-word",
                    }}
                >
                    {filteredLines.length > 0 ? (
                        filteredLines.map((line, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: Math.min(index * 0.01, 0.3) }}
                                className={`
                                    ${line.includes("ERROR") || line.includes("error") ? "text-rose-400" : ""}
                                    ${line.includes("WARN") || line.includes("warn") ? "text-amber-400" : ""}
                                    ${line.includes("INFO") || line.includes("info") ? "text-cyan-400" : ""}
                                    ${line.includes("✓") || line.includes("SUCCESS") ? "text-emerald-400" : ""}
                                `}
                            >
                                {line}
                            </motion.div>
                        ))
                    ) : (
                        <span className="text-slate-600">No logs match your search criteria.</span>
                    )}
                </pre>
            </motion.div>

            {/* Footer Stats */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="border-t border-white/10 bg-slate-900/50 px-4 py-2 flex items-center justify-between text-[10px] text-slate-500"
            >
                <span>
                    Showing {filteredLines.length} of {lines.length} lines
                </span>
                <span>{Math.round(content.length / 1024)} KB</span>
            </motion.div>
        </motion.div>
    );
}
