"use client";

import { useEffect, useState } from "react";
import { useHealth } from "@/hooks/useHealth";
import { useStatus } from "@/hooks/useStatus";
import { useRepository } from "@/hooks/useRepository";
import { useRepositoryAnalysis } from "@/hooks/useRepositoryAnalysis";
import { useExecutionStream } from "@/hooks/useExecutionStream";
import { useVerification } from "@/hooks/useVerification";
import { CommandCenter } from "@/components/dashboard/CommandCenter";
import { EnterpriseOverview } from "@/components/dashboard/EnterpriseOverview";
import type { RepositoryMetadata, TimelineEntry } from "@/types";
import { fetchPlatformOverview } from "@/services/api";
import type { PlatformOverview } from "@/types";

export default function DashboardPage() {
    const { isLoading: healthLoading, refetch: refetchHealth } = useHealth();
    const { status, isLoading: statusLoading, refetch: refetchStatus } = useStatus();
    const latestUploadId = status?.uploads[0]?.upload_id;
    const { repository, isLoading: repositoryLoading, error: repositoryError } = useRepository(latestUploadId);
    const { analysis, isLoading: analysisLoading, error: analysisError } = useRepositoryAnalysis(latestUploadId);
    const verification = useVerification(latestUploadId);
    const execution = useExecutionStream(latestUploadId, verification.fetch);
    const [platformOverview, setPlatformOverview] = useState<PlatformOverview | null>(null);

    useEffect(() => {
        if (latestUploadId && execution.status === "COMPLETED") void verification.fetch();
    }, [execution.status, latestUploadId, verification.fetch]);

    useEffect(() => {
        if (!latestUploadId) return;
        void fetchPlatformOverview(latestUploadId).then(setPlatformOverview).catch(() => setPlatformOverview(null));
    }, [latestUploadId]);

    return <>
        <div className="mx-auto max-w-[1480px] px-4 pt-8 sm:px-6 lg:px-10">
            <EnterpriseOverview repositoryName={repository?.repository_name} isRunning={execution.isRunning} overview={platformOverview} />
        </div>
        <CommandCenter
            repository={repository}
            analysis={analysis}
            report={verification.report}
            events={execution.events}
            executionStatus={execution.status}
            workflowState={execution.workflowState}
            currentStage={execution.currentStage}
            progress={execution.progress}
            elapsedSeconds={execution.elapsedSeconds}
            isRunning={execution.isRunning}
            onStart={execution.start}
            timeline={buildTimeline(repository, repositoryLoading, Boolean(latestUploadId))}
            uploads={status?.uploads ?? []}
            uploadsLoading={statusLoading}
            repositoryLoading={repositoryLoading}
            analysisLoading={analysisLoading}
            healthLoading={healthLoading}
            repositoryError={repositoryError}
            analysisError={analysisError}
            onRefresh={() => { refetchHealth(); refetchStatus(); }}
        />
    </>;
}

function buildTimeline(repository: RepositoryMetadata | null, loading: boolean, hasUpload: boolean): TimelineEntry[] {
    return [
        { id: "1", label: "Artifact received", status: hasUpload ? "done" : "pending" },
        { id: "2", label: "Repository analyzed", status: loading ? "running" : repository ? "done" : "pending" },
        { id: "3", label: "Project metadata detected", status: repository ? "done" : "pending" },
        { id: "4", label: "Execution verification", status: "pending" },
    ];
}
