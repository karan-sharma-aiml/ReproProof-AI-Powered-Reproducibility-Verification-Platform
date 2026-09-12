import axios from "axios";
import type {
  HealthResponse,
  RepositoryMetadata,
  RepositoryAIAnalysis,
  FinalVerificationReport,
  StatusResponse,
  UploadResponse,
  TroubleshootingReport,
  PatchResult,
  ApplyResult,
  RollbackResult,
  RerunResult,
  AnalyticsResult,
  ExecutiveSummary,
  HealthScoreResult,
} from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 30_000,
  headers: { Accept: "application/json" },
});

/* ── Health ─────────────────────────────────────────────────────────────── */

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

/* ── Upload ─────────────────────────────────────────────────────────────── */

export async function uploadFile(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);

  const { data } = await api.post<UploadResponse>("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress(event) {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });
  return data;
}

/* ── Status ─────────────────────────────────────────────────────────────── */

export async function fetchStatus(): Promise<StatusResponse> {
  const { data } = await api.get<StatusResponse>("/status");
  return data;
}

export async function fetchRepository(
  repositoryId: string,
): Promise<RepositoryMetadata> {
  const { data } = await api.get<RepositoryMetadata>(`/repository/${repositoryId}`);
  return data;
}

export async function fetchRepositoryAnalysis(
  repositoryId: string,
): Promise<RepositoryAIAnalysis> {
  const { data } = await api.get<RepositoryAIAnalysis>(`/analysis/${repositoryId}`);
  return data;
}

export async function fetchVerification(
  repositoryId: string,
): Promise<FinalVerificationReport> {
  const { data } = await api.get<{ report: FinalVerificationReport; markdown: string }>(`/report/${repositoryId}`);
  const report = data.report as FinalVerificationReport & {
    final_ai_confidence?: number;
  };
  return {
    ...report,
    confidence: report.final_ai_confidence ?? report.confidence ?? 0,
  };
}

export async function troubleshootExecution(
  executionId: string,
): Promise<TroubleshootingReport> {
  const { data } = await api.post<TroubleshootingReport>("/troubleshoot", {
    execution_id: executionId,
  });
  return data;
}

export async function generatePatch(executionId: string): Promise<PatchResult> {
  const { data } = await api.post<PatchResult>("/generate-patch", {
    execution_id: executionId,
  });
  return data;
}

export async function applyFix(executionId: string, patchId: string): Promise<ApplyResult> {
  const { data } = await api.post<ApplyResult>("/apply-fix", {
    execution_id: executionId,
    patch_id: patchId,
  });
  return data;
}

export async function rerunExecution(executionId: string): Promise<RerunResult> {
  const { data } = await api.post<RerunResult>("/rerun", { execution_id: executionId });
  return data;
}

export async function rollbackExecution(executionId: string): Promise<RollbackResult> {
  const { data } = await api.post<RollbackResult>("/rollback", { execution_id: executionId });
  return data;
}

export async function fetchAnalytics(): Promise<AnalyticsResult> {
  const { data } = await api.get<AnalyticsResult>("/analytics");
  return data;
}

export async function fetchHealthScore(repositoryId: string): Promise<HealthScoreResult> {
  const { data } = await api.get<HealthScoreResult>(`/health-score/${repositoryId}`);
  return data;
}

export async function fetchExecutiveSummary(repositoryId: string): Promise<ExecutiveSummary> {
  const { data } = await api.get<ExecutiveSummary>(`/summary/${repositoryId}`);
  return data;
}

export default api;
