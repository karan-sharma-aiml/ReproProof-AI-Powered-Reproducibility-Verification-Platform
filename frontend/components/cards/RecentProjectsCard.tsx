"use client";

import { FolderOpen } from "lucide-react";
import { formatBytes, formatDate } from "@/utils/format";
import type { UploadSummary } from "@/types";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

interface RecentProjectsCardProps {
  uploads: UploadSummary[];
  isLoading: boolean;
}

export function RecentProjectsCard({ uploads, isLoading }: RecentProjectsCardProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center gap-3 mb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50 text-purple-600 dark:bg-purple-950 dark:text-purple-400">
          <FolderOpen className="h-5 w-5" />
        </div>
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
          Recent Projects
        </h3>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-6">
          <LoadingSpinner size="sm" />
        </div>
      ) : uploads.length === 0 ? (
        <p className="py-6 text-center text-sm text-gray-400 dark:text-gray-500">
          No uploads yet
        </p>
      ) : (
        <ul className="divide-y divide-gray-100 dark:divide-gray-800">
          {uploads.slice(0, 5).map((u) => (
            <li key={u.filename} className="flex items-center justify-between py-2.5">
              <span className="truncate text-sm text-gray-700 dark:text-gray-300">
                {u.filename}
              </span>
              <span className="shrink-0 ml-3 text-xs text-gray-400 dark:text-gray-500">
                {formatBytes(u.size_bytes)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
