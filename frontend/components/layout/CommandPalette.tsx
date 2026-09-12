"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Search, Upload, Play, FileText, Wrench, BarChart3, RotateCcw, Settings, Moon, Sun, Command } from "lucide-react";
import { useEffect, useState } from "react";
import Link from "next/link";

interface Command {
    id: string;
    title: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    action?: () => void;
    href?: string;
    category: string;
}

export function CommandPalette() {
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState("");

    const commands: Command[] = [
        {
            id: "upload",
            title: "Upload Repository",
            description: "Upload a new repository for analysis",
            icon: Upload,
            href: "/",
            category: "Actions",
        },
        {
            id: "run",
            title: "Run Verification",
            description: "Start a new verification run",
            icon: Play,
            category: "Actions",
        },
        {
            id: "analytics",
            title: "Open Analytics",
            description: "View platform analytics and metrics",
            icon: BarChart3,
            href: "/analytics",
            category: "Navigation",
        },
        {
            id: "troubleshooting",
            title: "Troubleshooting",
            description: "Access troubleshooting tools",
            icon: Wrench,
            href: "/troubleshooting",
            category: "Navigation",
        },
        {
            id: "report",
            title: "Generate Report",
            description: "Create a detailed analysis report",
            icon: FileText,
            category: "Actions",
        },
        {
            id: "refresh",
            title: "Refresh Workspace",
            description: "Reload all data from the server",
            icon: RotateCcw,
            category: "Workspace",
        },
        {
            id: "settings",
            title: "Settings",
            description: "Configure application settings",
            icon: Settings,
            category: "Workspace",
        },
        {
            id: "theme",
            title: "Toggle Theme",
            description: "Switch between light and dark mode",
            icon: Moon,
            category: "Workspace",
        },
    ];

    const filtered = commands.filter(
        (cmd) =>
            cmd.title.toLowerCase().includes(search.toLowerCase()) ||
            cmd.description.toLowerCase().includes(search.toLowerCase())
    );

    const grouped = filtered.reduce(
        (acc, cmd) => {
            if (!acc[cmd.category]) acc[cmd.category] = [];
            acc[cmd.category].push(cmd);
            return acc;
        },
        {} as Record<string, Command[]>
    );

    // Keyboard shortcut
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "k") {
                e.preventDefault();
                setOpen(!open);
                setSearch("");
            }
            if (e.key === "Escape") {
                setOpen(false);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [open]);

    return (
        <AnimatePresence>
            {open && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={() => setOpen(false)}
                    className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
                >
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -20 }}
                        onClick={(e) => e.stopPropagation()}
                        className="fixed left-1/2 top-1/4 w-full max-w-2xl -translate-x-1/2 rounded-2xl border border-white/10 bg-slate-950/95 shadow-2xl overflow-hidden"
                    >
                        {/* Input */}
                        <div className="border-b border-white/10 bg-slate-900/50 px-4 py-4">
                            <div className="flex items-center gap-3">
                                <Search className="h-5 w-5 text-slate-500" />
                                <input
                                    autoFocus
                                    type="text"
                                    placeholder="Search commands..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    className="w-full border-0 bg-transparent text-lg text-slate-200 placeholder:text-slate-600 focus:outline-none"
                                />
                            </div>
                        </div>

                        {/* Results */}
                        <div className="max-h-96 overflow-y-auto">
                            {Object.entries(grouped).length > 0 ? (
                                Object.entries(grouped).map(([category, cmds]) => (
                                    <motion.div key={category}>
                                        <div className="px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-slate-600">
                                            {category}
                                        </div>
                                        {cmds.map((cmd, index) => (
                                            <CommandItem key={cmd.id} command={cmd} onSelect={() => setOpen(false)} />
                                        ))}
                                    </motion.div>
                                ))
                            ) : (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="px-4 py-8 text-center text-sm text-slate-500"
                                >
                                    No commands found.
                                </motion.div>
                            )}
                        </div>

                        {/* Footer */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.1 }}
                            className="border-t border-white/10 bg-slate-900/50 px-4 py-3 flex items-center justify-between text-[10px] text-slate-600"
                        >
                            <span>Use arrow keys to navigate • Enter to select</span>
                            <span className="flex items-center gap-1">
                                <Command className="h-3 w-3" /> K to close
                            </span>
                        </motion.div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

function CommandItem({ command, onSelect }: { command: Command; onSelect: () => void }) {
    const Icon = command.icon;
    const content = (
        <motion.div
            whileHover={{ backgroundColor: "rgba(255,255,255,0.05)" }}
            className="flex items-center gap-4 px-4 py-3 cursor-pointer border-b border-white/5 last:border-b-0 transition"
        >
            <Icon className="h-5 w-5 text-violet-400" />
            <div className="flex-1">
                <p className="text-sm font-medium text-slate-200">{command.title}</p>
                <p className="text-xs text-slate-600">{command.description}</p>
            </div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-600 opacity-50">
                Enter
            </div>
        </motion.div>
    );

    if (command.href) {
        return (
            <Link href={command.href} onClick={onSelect}>
                {content}
            </Link>
        );
    }

    return <div onClick={() => { command.action?.(); onSelect(); }}>{content}</div>;
}
