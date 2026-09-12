"use client";

export function Footer() {
  return (
    <footer className="border-t border-white/[0.08] bg-[#070B17] dark:border-white/[0.08] dark:bg-[#070B17]">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 px-4 py-6 sm:flex-row sm:px-6 lg:px-8">
        <p className="text-sm text-slate-500 dark:text-slate-400">
          &copy; {new Date().getFullYear()} ReproProof. Built for reproducibility.
        </p>
        <p className="text-xs text-slate-600 dark:text-slate-500">
          Agentic AI Hackathon Project
        </p>
      </div>
    </footer>
  );
}
