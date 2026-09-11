"use client";

import { useEffect, useState } from "react";
import { fetchRepositoryAnalysis } from "@/services/api";
import type { RepositoryAIAnalysis } from "@/types";

export function useRepositoryAnalysis(repositoryId?: string) {
    const [analysis, setAnalysis] = useState<RepositoryAIAnalysis | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!repositoryId) {
            setAnalysis(null);
            setError(null);
            setIsLoading(false);
            return;
        }
        let active = true;
        setIsLoading(true);
        fetchRepositoryAnalysis(repositoryId)
            .then((data) => active && setAnalysis(data))
            .catch(() => active && setError("AI repository analysis unavailable"))
            .finally(() => active && setIsLoading(false));
        return () => {
            active = false;
        };
    }, [repositoryId]);

    return { analysis, isLoading, error };
}