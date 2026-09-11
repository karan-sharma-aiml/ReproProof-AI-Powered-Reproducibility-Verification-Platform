"use client";

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 px-4 py-6 sm:flex-row sm:px-6 lg:px-8">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          &copy; {new Date().getFullYear()} ReproProof. Built for reproducibility.
        </p>
        <p className="text-xs text-gray-400 dark:text-gray-500">
          Agentic AI Hackathon Project
        </p>
      </div>
    </footer>
  );
}
