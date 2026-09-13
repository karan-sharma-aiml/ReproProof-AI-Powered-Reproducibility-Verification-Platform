"use client";

import { useEffect, useRef, useState } from "react";
import type { ExecutionEvent, FinalVerificationReport } from "@/types";

type ExecutionStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILED" | "TIMEOUT" | "CANCELLED" | "COMPLETED" | "SKIPPED";
export type WorkflowState = "OBSERVING" | "PLANNING" | "EXECUTING" | "VERIFYING" | "PATCHING" | "COMPLETED" | "FAILED";

export function useExecutionStream(
    repositoryId?: string,
    onVerificationReady?: () => Promise<FinalVerificationReport | null> | void,
) {
    const sourceRef = useRef<EventSource | null>(null);
    const [events, setEvents] = useState<ExecutionEvent[]>([]);
    const [status, setStatus] = useState<ExecutionStatus>("PENDING");
    const [isRunning, setIsRunning] = useState(false);
    const [startedAt, setStartedAt] = useState<number | null>(null);

    function workflowState(): WorkflowState {
        const stage = events.at(-1)?.stage ?? "";
        if (status === "FAILED") return "FAILED";
        if (status === "COMPLETED" || status === "SUCCESS" || status === "SKIPPED") return "COMPLETED";
        if (stage === "REPOSITORY_ANALYSIS_COMPLETE") return "OBSERVING";
        if (stage === "EXECUTION_PLAN_GENERATED") return "PLANNING";
        if (["HEALTH_CHECK_SUCCESS", "EXECUTION_COMPLETE", "REPORT_GENERATED"].includes(stage)) return "VERIFYING";
        if (stage === "PATCH_APPLY" || stage === "RERUN") return "PATCHING";
        if (stage === "EXECUTION_STARTED" || stage === "SERVER_STARTED" || stage === "DEPENDENCIES_INSTALLED") return "EXECUTING";
        return isRunning ? "OBSERVING" : "OBSERVING";
    }

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

            if (event.stage === "EXECUTION_SKIPPED") {
                setStatus("SKIPPED");
            }

            if (event.stage === "VERIFICATION_READY") {
                setStatus((current) => current === "SKIPPED" ? "SKIPPED" : event.status === "SUCCESS" ? "COMPLETED" : "FAILED");
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
    return { events, status, workflowState: workflowState(), isRunning, progress, currentStage, elapsedSeconds, start };
}