"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "@/hooks/useTheme";
import { Bell, Moon, Sun, Shield, Sparkles } from "lucide-react";

export function Header() {
  const { theme, toggle } = useTheme();
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 bg-white/80 backdrop-blur-2xl dark:border-white/[0.08] dark:bg-[#070B17]/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3 rounded-xl">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 text-white shadow-lg shadow-blue-500/20"><Shield className="h-5 w-5" /></span>
          <span><span className="block text-sm font-semibold tracking-tight text-slate-950 dark:text-white">ReproProof</span><span className="hidden text-[10px] uppercase tracking-[0.16em] text-slate-500 sm:block">AI reproducibility control plane</span></span>
        </Link>

        <nav className="flex items-center gap-2 sm:gap-4">
          <Link
            href="/"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium sm:block ${pathname === "/" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Home
          </Link>
          <Link
            href="/dashboard"
            className={`rounded-lg px-2.5 py-2 text-sm font-medium ${pathname === "/dashboard" ? "bg-white/[0.08] text-white" : "text-slate-300 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Dashboard
          </Link>
          <Link
            href="/troubleshooting"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium md:block ${pathname === "/troubleshooting" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Troubleshooting
          </Link>
          <Link
            href="/analytics"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium md:block ${pathname === "/analytics" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Analytics
          </Link>
          <Link
            href="/assistant"
            aria-label="Open AI assistant"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium lg:block ${pathname === "/assistant" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Assistant
          </Link>
          <Link
            href="/judge-mode"
            aria-label="Open judge mode"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium xl:block ${pathname === "/judge-mode" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Judge Mode
          </Link>
          <Link
            href="/demo"
            aria-label="Open judge demo mode"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium lg:block ${pathname === "/demo" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Demo
          </Link>
          <Link
            href="/executive"
            aria-label="Open executive summary"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium xl:block ${pathname === "/executive" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Executive
          </Link>
          <Link
            href="/providers"
            aria-label="Open AI provider status"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium 2xl:block ${pathname === "/providers" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Providers
          </Link>
          <Link
            href="/infrastructure"
            aria-label="Open infrastructure status"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium 2xl:block ${pathname === "/infrastructure" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Infra
          </Link>
          <Link
            href="/monitoring"
            aria-label="Open monitoring dashboard"
            className={`hidden rounded-lg px-2.5 py-2 text-sm font-medium 2xl:block ${pathname === "/monitoring" ? "bg-white/[0.08] text-white" : "text-slate-400 hover:bg-white/[0.05] hover:text-white"}`}
          >
            Monitoring
          </Link>
          <span className="hidden items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-300 lg:flex"><Sparkles className="h-3 w-3" /> Systems nominal</span>
          <button type="button" aria-label="Notifications" className="rounded-lg p-2 text-slate-400 hover:bg-white/[0.06] hover:text-white">
            <Bell className="h-4 w-4" />
          </button>
          <button type="button" onClick={toggle} className="rounded-lg p-2 text-slate-400 hover:bg-white/[0.06] hover:text-white"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </button>
        </nav>
      </div>
    </header>
  );
}
