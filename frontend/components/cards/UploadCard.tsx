"use client";

import { Upload, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/utils/cn";
import { formatBytes, formatDate } from "@/utils/format";
import type { UploadData } from "@/types";

interface UploadCardProps {
  data: UploadData;
}

export function UploadCard({ data }: UploadCardProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-950 dark:text-brand-400">
          <Upload className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-gray-900 dark:text-white">
            {data.original_filename}
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {formatBytes(data.size_bytes)} &middot; {formatDate(data.uploaded_at)}
          </p>
          <div className="mt-2 flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            <span className="text-xs font-medium text-green-600 dark:text-green-400">
              Uploaded
            </span>
          </div>
        </div>
      </div>
      <div className="mt-3 rounded-md bg-gray-50 px-3 py-2 dark:bg-gray-800">
        <p className="truncate font-mono text-xs text-gray-500 dark:text-gray-400">
          ID: {data.upload_id}
        </p>
      </div>
    </div>
  );
}
