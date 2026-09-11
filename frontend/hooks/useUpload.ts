"use client";

import { useCallback, useState } from "react";
import { uploadFile } from "@/services/api";
import type { UploadData } from "@/types";

interface UseUploadReturn {
  isUploading: boolean;
  progress: number;
  error: string | null;
  data: UploadData | null;
  upload: (file: File) => Promise<UploadData | null>;
  reset: () => void;
}

export function useUpload(): UseUploadReturn {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<UploadData | null>(null);

  const reset = useCallback(() => {
    setIsUploading(false);
    setProgress(0);
    setError(null);
    setData(null);
  }, []);

  const upload = useCallback(async (file: File): Promise<UploadData | null> => {
    setIsUploading(true);
    setProgress(0);
    setError(null);
    setData(null);

    try {
      const res = await uploadFile(file, setProgress);
      setData(res.data);
      return res.data;
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } })?.response?.data
          ?.error ?? "Upload failed. Please try again.";
      setError(msg);
      return null;
    } finally {
      setIsUploading(false);
    }
  }, []);

  return { isUploading, progress, error, data, upload, reset };
}
