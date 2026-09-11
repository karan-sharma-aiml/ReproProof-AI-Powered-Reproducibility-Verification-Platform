"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchHealth } from "@/services/api";
import type { HealthResponse } from "@/types";

interface UseHealthReturn {
  health: HealthResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useHealth(pollIntervalMs = 30_000): UseHealthReturn {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch {
      setError("Backend unreachable");
      setHealth(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
    const id = setInterval(refetch, pollIntervalMs);
    return () => clearInterval(id);
  }, [refetch, pollIntervalMs]);

  return { health, isLoading, error, refetch };
}
