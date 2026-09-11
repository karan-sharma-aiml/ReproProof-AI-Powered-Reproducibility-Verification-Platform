"use client";

import { useEffect, useRef, useState } from "react";
import type { ExecutionEvent, FinalVerificationReport } from "@/types";

type ExecutionStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILED" | "TIMEOUT" | "CANCELLED" | "COMPLETED";

export function useExecutionStream(
    repositoryId?: string,
    onVerificationReady?: () => Promise<FinalVerificationReport | null> | void,
) {
    const sourceRef = useRef<EventSource | null>(null);
    const [events, setEvents] = useState<ExecutionEvent[]>([]);
    const [status, setStatus] = useState<ExecutionStatus>("PENDING");
    const [isRunning, setIsRunning] = useState(false);
    const [startedAt, setStartedAt] = useState<number | null>(null);

    function start() {
        if (!repositoryId || sourceRef.current) return;
        setEvents([]);
        setStatus("RUNNING");
        setIsRunning(true);
        setStartedAt(Date.now());
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
        const source = new EventSource(`${baseUrl}/execution/${repositoryId}/stream`);
        sourceRef.current = source;

        source.onmessage = (message) => {
            const event = JSON.parse(message.data) as ExecutionEvent;
            setEvents((current) => [...current, event]);

            if (event.stage === "VERIFICATION_READY") {
                setStatus(event.status === "SUCCESS" ? "COMPLETED" : "FAILED");
                setIsRunning(false);
                if (sourceRef.current) {
                    sourceRef.current.close();
                    sourceRef.current = null;
                }
                if (onVerificationReady) {
                    void Promise.resolve(onVerificationReady()).finally(() => {
                        setIsRunning(false);
                    });
                }
                return;
            }
        };

        source.onerror = () => {
            setStatus("FAILED");
            setIsRunning(false);
            if (sourceRef.current) {
                sourceRef.current.close();
                sourceRef.current = null;
            }
        };
    }

    useEffect(() => () => sourceRef.current?.close(), []);

    const progress = events.length ? events[events.length - 1].progress : 0;
    const currentStage = events.length ? events[events.length - 1].stage : "PENDING";
    const elapsedSeconds = startedAt ? Math.max(0, Math.floor((Date.now() - startedAt) / 1000)) : 0;
    return { events, status, isRunning, progress, currentStage, elapsedSeconds, start };
}