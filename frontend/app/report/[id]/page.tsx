"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, FileText } from "lucide-react";
import { fetchVerification } from "@/services/api";
import { VerificationResultPanel } from "@/components/dashboard/VerificationResultPanel";
import type { FinalVerificationReport } from "@/types";

export default function ReportPage() {
    const params = useParams<{ id: string }>();
    const reportId = params.id;
    const [report, setReport] = useState<FinalVerificationReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let active = true;
        async function loadReport() {
            if (!reportId) return;
            try {
                const result = await fetchVerification(reportId);
                if (active) setReport(result);
            } catch {
                if (active) setError("This verification report is still being prepared.");
            } finally {
                if (active) setLoading(false);
            }
        }
        void loadReport();
        return () => {
            active = false;
        };
    }, [reportId]);

    return <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-10">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-violet-300" />
                <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-300">Verification report</p><h1 className="mt-1 text-2xl font-semibold text-white">Report {reportId}</h1></div>
            </div>
            <Link href="/dashboard" className="action-button"><ArrowLeft className="h-4 w-4" /> Back to dashboard</Link>
        </div>
        {loading ? <p className="text-sm text-slate-400">Loading report...</p> : <VerificationResultPanel report={report} error={error} />}
    </main>;
}
