import axios from "axios";
import type {
  HealthResponse,
  RepositoryMetadata,
  RepositoryAIAnalysis,
  FinalVerificationReport,
  StatusResponse,
  UploadResponse,
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
  return data.report;
}

export default api;
