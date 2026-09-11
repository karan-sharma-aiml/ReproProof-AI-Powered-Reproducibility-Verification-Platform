"use client";

import { cn } from "@/utils/cn";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizes = {
  sm: "h-4 w-4 border-2",
  md: "h-8 w-8 border-[3px]",
  lg: "h-12 w-12 border-4",
};

export function LoadingSpinner({ size = "md", className }: LoadingSpinnerProps) {
  return (
    <div
      className={cn(
        "animate-spin rounded-full border-gray-300 border-t-brand-600 dark:border-gray-600 dark:border-t-brand-400",
        sizes[size],
        className,
      )}
      role="status"
      aria-label="Loading"
    />
  );
}
