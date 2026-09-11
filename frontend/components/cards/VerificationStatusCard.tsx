"use client";

import { cn } from "@/utils/cn";
import { Shield, ShieldCheck, ShieldX, Loader2 } from "lucide-react";
import type { VerificationState } from "@/types";

interface VerificationStatusCardProps {
  state: VerificationState;
  filename?: string;
}

const config: Record<
  VerificationState,
  { icon: typeof Shield; label: string; color: string; bg: string }
> = {
  idle: {
    icon: Shield,
    label: "Ready to verify",
    color: "text-gray-500 dark:text-gray-400",
    bg: "bg-gray-100 dark:bg-gray-800",
  },
  uploading: {
    icon: Loader2,
    label: "Uploading…",
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-50 dark:bg-blue-950",
  },
  verifying: {
    icon: Loader2,
    label: "Verifying…",
    color: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-50 dark:bg-amber-950",
  },
  success: {
    icon: ShieldCheck,
    label: "Verification passed",
    color: "text-green-600 dark:text-green-400",
    bg: "bg-green-50 dark:bg-green-950",
  },
  failed: {
    icon: ShieldX,
    label: "Verification failed",
    color: "text-red-600 dark:text-red-400",
    bg: "bg-red-50 dark:bg-red-950",
  },
};

export function VerificationStatusCard({ state, filename }: VerificationStatusCardProps) {
  const { icon: Icon, label, color, bg } = config[state];
  const spinning = state === "uploading" || state === "verifying";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center gap-4">
        <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl", bg)}>
          <Icon className={cn("h-6 w-6", color, spinning && "animate-spin")} />
        </div>
        <div>
          <p className={cn("text-sm font-semibold", color)}>{label}</p>
          {filename && (
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              {filename}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
