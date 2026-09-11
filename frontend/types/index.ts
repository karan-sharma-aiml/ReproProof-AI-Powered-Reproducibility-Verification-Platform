/* ── API response types (mirrors backend Pydantic schemas) ─────────────── */

export interface BaseResponse {
  success: boolean;
  message: string;
}

/* GET / */
export interface RootResponse extends BaseResponse {
  app: string;
  version: string;
  docs: string;
}

/* GET /health */
export interface HealthResponse extends BaseResponse {
  status: string;
  environment: string;
  timestamp: string;
}

/* POST /upload */
export interface UploadData {
  upload_id: string;
  original_filename: string;
  saved_filename: string;
  size_bytes: number;
  uploaded_at: string;
  repository_path?: string;
}

export interface UploadResponse extends BaseResponse {
  data: UploadData;
}

/* GET /status */
export interface UploadSummary {
  upload_id: string;
  filename: string;
  size_bytes: number;
  uploaded_at: string;
}

export interface RepositoryMetadata {
  repository_name: string;
  repository_id: string;
  repository_path: string;
  total_files: number;
  total_folders: number;
  python_files: number;
  notebooks: number;
  important_files: string[];
  source_directories: string[];
  detected_languages: string[];
  tree: string[];
  datasets: string[];
  detected_frameworks: string[];
  health_score: number;
  warnings: string[];
}

export type IssueSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface RepositoryIssue {
  issue_type: string;
  title: string;
  description: string;
  severity: IssueSeverity;
  confidence: number;
  reason: string;
  recommended_fix: string;
  evidence: string[];
  affected_file: string;
}

export interface RepositoryAIAnalysis {
  repository_id: string;
  repository_name: string;
  issues: RepositoryIssue[];
  execution_probability: number;
  reproducibility_score: number;
  risk_score: number;
  summary: string;
}

export interface ExecutionEvent {
  stage: string;
  status: "RUNNING" | "SUCCESS" | "FAILED";
  timestamp: string;
  message: string;
  progress: number;
  stream: "stdout" | "stderr" | "system";
}

export interface VerificationReport {
  expected_value: number;
  actual_value: number | null;
  metric_name: string;
  absolute_difference: number | null;
  relative_difference: number | null;
  tolerance: number;
  reproduced: boolean;
  confidence: number;
  verdict: string;
  explanation: string;
  matched_metrics: Record<string, number>;
  failed_metrics: Record<string, number>;
  missing_metrics: string[];
  overall_similarity: number;
  overall_score: number;
}

export interface FinalVerificationReport {
  repository: RepositoryMetadata;
  static_analysis: RepositoryAIAnalysis;
  execution: Record<string, unknown>;
  metrics: Record<string, number>;
  verification: VerificationReport;
  verdict: "REPRODUCED" | "PARTIALLY_REPRODUCED" | "NOT_REPRODUCED" | "EXECUTION_FAILED" | "INVALID_PROJECT";
  confidence: number;
  overall_score: number;
  explanation: string;
  repair_suggestions: string[];
  timestamp: string;
  system_information: string;
  markdown_report: string;
}

export interface StatusResponse extends BaseResponse {
  environment: string;
  uploads_dir: string;
  reports_dir: string;
  total_uploads: number;
  uploads: UploadSummary[];
}

export interface ErrorResponse {
  success: false;
  error: string;
}

/* ── UI types ────────────────────────────────────────────────────────────── */

export type ToastVariant = "success" | "error" | "info" | "warning";

export interface Toast {
  id: string;
  variant: ToastVariant;
  title: string;
  description?: string;
}

export type VerificationState =
  | "idle"
  | "uploading"
  | "verifying"
  | "success"
  | "failed";

export interface TimelineEntry {
  id: string;
  label: string;
  status: "pending" | "running" | "done" | "error";
  timestamp?: string;
}

export interface RecentProject {
  id: string;
  name: string;
  status: VerificationState;
  uploadedAt: string;
  sizeBytes: number;
}
