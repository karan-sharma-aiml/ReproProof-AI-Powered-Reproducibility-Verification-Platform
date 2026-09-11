"use client";

import { useCallback, useState } from "react";
import { fetchVerification } from "@/services/api";
import type { FinalVerificationReport } from "@/types";

const RETRY_DELAYS_MS = [250, 500, 1000];

export function useVerification(repositoryId?: string) {
    const [report, setReport] = useState<FinalVerificationReport | null>(null);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        if (!repositoryId) return null;

        let attempt = 0;
        while (attempt < RETRY_DELAYS_MS.length + 1) {
            try {
                const data = await fetchVerification(repositoryId);
                setReport(data);
                setError(null);
                return data;
            } catch {
                if (attempt >= RETRY_DELAYS_MS.length) {
                    setError("No final verification report is available yet");
                    return null;
                }

                const delay = RETRY_DELAYS_MS[attempt];
                await new Promise((resolve) => setTimeout(resolve, delay));
                attempt += 1;
            }
        }

        setError("No final verification report is available yet");
        return null;
    }, [repositoryId]);

    return { report, error, fetch: load };
}