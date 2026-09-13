"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchStatus } from "@/services/api";
import type { StatusResponse } from "@/types";

interface UseStatusReturn {
  status: StatusResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useStatus(): UseStatusReturn {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchStatus();
      setStatus(data);
    } catch {
      setError("Failed to fetch status");
      setStatus(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { status, isLoading, error, refetch };
}
