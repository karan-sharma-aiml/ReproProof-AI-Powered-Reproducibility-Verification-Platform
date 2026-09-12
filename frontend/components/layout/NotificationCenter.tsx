"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Bell, CheckCircle2, AlertCircle, Info, X } from "lucide-react";
import { useState, useCallback } from "react";

export interface Notification {
    id: string;
    title: string;
    message: string;
    type: "success" | "error" | "warning" | "info";
    timestamp: number;
    duration?: number;
}

export function useNotifications() {
    const [notifications, setNotifications] = useState<Notification[]>([]);

    const addNotification = useCallback(
        (title: string, message: string, type: "success" | "error" | "warning" | "info" = "info", duration = 5000) => {
            const id = `notification-${Date.now()}`;
            const notification: Notification = {
                id,
                title,
                message,
                type,
                timestamp: Date.now(),
                duration,
            };

            setNotifications((prev) => [...prev, notification]);

            if (duration > 0) {
                setTimeout(() => {
                    removeNotification(id);
                }, duration);
            }

            return id;
        },
        []
    );

    const removeNotification = useCallback((id: string) => {
        setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, []);

    return { notifications, addNotification, removeNotification };
}

export function NotificationCenter({
    notifications,
    onRemove,
}: {
    notifications: Notification[];
    onRemove: (id: string) => void;
}) {
    const [showCenter, setShowCenter] = useState(false);
    const unreadCount = notifications.length;

    const typeConfig = {
        success: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-400/10" },
        error: { icon: AlertCircle, color: "text-rose-400", bg: "bg-rose-400/10" },
        warning: { icon: AlertCircle, color: "text-amber-400", bg: "bg-amber-400/10" },
        info: { icon: Info, color: "text-cyan-400", bg: "bg-cyan-400/10" },
    };

    return (
        <div className="fixed bottom-6 right-6 z-40">
            {/* Bell Icon Button */}
            <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowCenter(!showCenter)}
                className="relative flex items-center justify-center w-12 h-12 rounded-full border border-white/10 bg-white/[0.04] hover:bg-white/[0.08] transition"
            >
                <Bell className="h-5 w-5 text-slate-300" />
                {unreadCount > 0 && (
                    <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute -top-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-rose-400 text-xs font-bold text-white"
                    >
                        {Math.min(unreadCount, 9)}+
                    </motion.span>
                )}
            </motion.button>

            {/* Notification Panel */}
            <AnimatePresence>
                {showCenter && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="absolute bottom-16 right-0 w-80 rounded-2xl border border-white/10 bg-slate-950/95 shadow-2xl overflow-hidden"
                    >
                        {/* Header */}
                        <div className="border-b border-white/10 bg-slate-900/50 px-4 py-3 flex items-center justify-between">
                            <p className="text-sm font-semibold text-white">Notifications</p>
                            {unreadCount > 0 && (
                                <span className="text-xs font-semibold text-slate-500">{unreadCount} new</span>
                            )}
                        </div>

                        {/* Notifications List */}
                        <div className="max-h-96 overflow-y-auto">
                            {notifications.length > 0 ? (
                                notifications.map((notification) => {
                                    const config = typeConfig[notification.type];
                                    const Icon = config.icon;

                                    return (
                                        <motion.div
                                            key={notification.id}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: 20 }}
                                            className="border-b border-white/5 p-4 hover:bg-white/[0.02] transition group"
                                        >
                                            <div className="flex gap-3">
                                                <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${config.bg}`}>
                                                    <Icon className={`h-4 w-4 ${config.color}`} />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-semibold text-white">{notification.title}</p>
                                                    <p className="mt-0.5 text-xs text-slate-500 line-clamp-2">{notification.message}</p>
                                                    <p className="mt-1 text-[10px] text-slate-600">
                                                        {new Date(notification.timestamp).toLocaleTimeString()}
                                                    </p>
                                                </div>
                                                <motion.button
                                                    whileHover={{ scale: 1.1 }}
                                                    whileTap={{ scale: 0.9 }}
                                                    onClick={() => onRemove(notification.id)}
                                                    className="mt-0.5 text-slate-600 hover:text-slate-300 opacity-0 group-hover:opacity-100 transition"
                                                >
                                                    <X className="h-4 w-4" />
                                                </motion.button>
                                            </div>
                                        </motion.div>
                                    );
                                })
                            ) : (
                                <div className="px-4 py-8 text-center text-sm text-slate-500">No notifications</div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Toast Notifications (Auto-dismiss) */}
            <AnimatePresence>
                {notifications.slice(-3).map((notification) => {
                    const config = typeConfig[notification.type];
                    const Icon = config.icon;

                    return (
                        <motion.div
                            key={notification.id}
                            initial={{ opacity: 0, y: 20, scale: 0.9 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 20, scale: 0.9 }}
                            className="absolute bottom-0 left-0 right-0 mb-2 mx-auto w-full max-w-sm rounded-xl border border-white/10 bg-slate-950/95 shadow-xl p-4"
                        >
                            <div className="flex gap-3">
                                <Icon className={`h-5 w-5 ${config.color} flex-shrink-0 mt-0.5`} />
                                <div className="flex-1">
                                    <p className="text-sm font-semibold text-white">{notification.title}</p>
                                    <p className="mt-0.5 text-xs text-slate-400">{notification.message}</p>
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </AnimatePresence>
        </div>
    );
}
