"use client";

import { useEffect, useState } from "react";
import type { PlatformProgressEvent } from "@/types";

export function usePlatformProgress(executionId?: string) {
    const [events, setEvents] = useState<PlatformProgressEvent[]>([]);

    useEffect(() => {
        if (!executionId) return;
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
        const socketUrl = `${baseUrl.replace(/^http/, "ws")}/ws/progress/${executionId}`;
        const socket = new WebSocket(socketUrl);
        socket.onmessage = (message) => {
            try {
                setEvents((current) => [...current, JSON.parse(message.data) as PlatformProgressEvent]);
            } catch {
                // Ignore malformed external events and keep the stream alive.
            }
        };
        return () => socket.close();
    }, [executionId]);

    return { events, latest: events.at(-1) ?? null };
}