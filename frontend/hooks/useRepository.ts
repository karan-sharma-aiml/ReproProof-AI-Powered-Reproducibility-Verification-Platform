"use client";

import { useEffect, useState } from "react";
import { fetchRepository } from "@/services/api";
import type { RepositoryMetadata } from "@/types";

export function useRepository(repositoryId?: string) {
    const [repository, setRepository] = useState<RepositoryMetadata | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!repositoryId) {
            setRepository(null);
            setError(null);
            setIsLoading(false);
            return;
        }

        let active = true;
        setIsLoading(true);
        setError(null);
        fetchRepository(repositoryId)
            .then((data) => {
                if (active) setRepository(data);
            })
            .catch(() => {
                if (active) {
                    setRepository(null);
                    setError("Repository analysis unavailable");
                }
            })
            .finally(() => {
                if (active) setIsLoading(false);
            });

        return () => {
            active = false;
        };
    }, [repositoryId]);

    return { repository, isLoading, error };
}