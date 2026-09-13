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

export interface MonitoringSnapshot {
  dashboard: { dashboards: { uid: string; title: string; panels: unknown[] }[]; health: { status: string; components: { name: string; status: string; reason: string }[] } };
  system: { metrics: { counters: Record<string, number>; histograms: Record<string, number[]>; system: Record<string, number> } };
  alerts: { groups: { name: string; rules: { alert: string; expr: string; labels: Record<string, string> }[] }[] };
  providers: { provider?: string; healthy?: boolean; configured?: boolean; reason?: string }[];
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

export interface GitHubVerificationResponse extends BaseResponse {
  data?: UploadData;
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
  package_managers?: string[];
  ci_cd?: string[];
  environment_files?: string[];
  licenses?: string[];
  test_frameworks?: string[];
  dependency_packages?: string[];
  docker_configured?: boolean;
  readme_quality?: number;
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

export type TroubleshootingSeverity = "Critical" | "High" | "Medium" | "Low" | "Info";

export interface TroubleshootingFinding {
  category: string;
  evidence: string[];
  confidence: number;
  severity: TroubleshootingSeverity;
}

export interface TroubleshootingReport {
  execution_id: string;
  root_cause: string;
  confidence: number;
  severity: TroubleshootingSeverity;
  explanation: string;
  possible_fixes: string[];
  requires_manual_action: boolean;
  detected_error: string;
  execution_log: string;
  findings: TroubleshootingFinding[];
}

export type PatchRiskLevel = "Low" | "Medium" | "High" | "Critical";

export interface PatchResult {
  patch_id: string;
  file_name: string;
  original_file: string;
  modified_file: string;
  git_unified_diff: string;
  summary: string;
  confidence: number;
  risk_level: PatchRiskLevel;
  estimated_success: number;
  warnings: string[];
  changed_files: string[];
  provider: string;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;
}

export interface ExecutionHistoryEntry {
  execution_id: string;
  attempt_number: number;
  patch_id: string;
  applied_files: string[];
  execution_status: string;
  timestamp: string;
  duration: number;
  reason: string;
  backup_path: string;
  execution: Record<string, unknown> | null;
}

export interface ApplyResult {
  execution_id: string;
  patch_id: string;
  status: "APPLIED";
  applied_files: string[];
  backup_location: string;
  verified: boolean;
}

export interface RollbackResult {
  execution_id: string;
  status: "ROLLED_BACK";
  restored_files: string[];
  backup_locations: string[];
}

export interface RerunResult {
  execution_id: string;
  final_status: string;
  retry_count: number;
  execution: Record<string, unknown>;
  history: ExecutionHistoryEntry[];
  applied_patch: PatchResult | null;
  backup_path: string;
  rollback_available: boolean;
}

export interface FinalVerificationReport {
  repository: RepositoryMetadata;
  static_analysis: RepositoryAIAnalysis;
  execution: Record<string, unknown>;
  metrics: Record<string, number>;
  verification: VerificationReport;
  workflow_status?: "SUCCESS" | "FAILED";
  verdict: "REPRODUCED" | "PARTIALLY_REPRODUCED" | "NOT_REPRODUCED" | "EXECUTION_FAILED" | "EXECUTION_SKIPPED" | "INVALID_PROJECT";
  confidence: number;
  final_ai_confidence?: number;
  confidence_factors?: string[];
  overall_score: number;
  explanation: string;
  repair_suggestions: string[];
  timestamp: string;
  system_information: string;
  markdown_report: string;
  troubleshooting?: TroubleshootingReport | null;
  generated_patch?: PatchResult | null;
  retry_count?: number;
  applied_patch?: PatchResult | null;
  execution_history?: ExecutionHistoryEntry[];
  backup_path?: string;
  rollback_available?: boolean;
  final_status?: string;
}

export interface AnalyticsResult {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  average_runtime: number;
  average_ai_confidence: number;
  patch_success_rate: number;
  retry_success_rate: number;
  most_common_errors: Record<string, number>;
  most_common_root_causes: Record<string, number>;
  top_missing_dependencies: Record<string, number>;
  language_distribution: Record<string, number>;
  framework_distribution: Record<string, number>;
  repository_statistics: Record<string, number>;
}

export interface HealthScoreResult {
  repository_id: string;
  score: number;
  recommendations: string[];
  dimensions: Record<string, number>;
}

export interface ExecutiveSummary {
  execution_id: string;
  summary: string;
  status: string;
  confidence: number;
  health_score: number;
}

export interface PlatformOverview {
  repository_id: string;
  verdict: string;
  overall_score: number;
  confidence: number;
  scores: Record<string, number>;
  workflow: { id: string; label: string; status: "complete" | "active" | "pending"; confidence: number }[];
  decision_tree: { label: string; value: string; children: { label: string; value: string }[] };
  recommendations: { title: string; reason: string; priority: "high" | "medium" | "low"; source: string }[];
  knowledge_graph: { nodes: unknown[]; edges: unknown[] };
}

export interface PlatformProgressEvent {
  execution_id: string;
  stage: string;
  status: "QUEUED" | "RUNNING" | "SUCCESS" | "FAILED" | "CANCELLED";
  progress: number;
  message: string;
  timestamp: string;
  eta_seconds: number | null;
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
