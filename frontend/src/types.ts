export type StepStatus =
  | "idle"
  | "running"
  | "success"
  | "retry"
  | "failure"
  | "escalated"
  | "stopped";

export interface CaseItem {
  caseId: string;
  title: string;
  filename: string;
  description: string;
  expectedOutput: string | null;
  group: "happy_path" | "governance" | "failure_case";
  badge: string;
  recommendedForVideo: boolean;
  code: string;
  path: string;
}

export interface TraceEvent {
  timestamp?: string;
  event?: string;
  handoff?: string;
  attempt_index?: number;
  summary?: string;
  payload?: Record<string, unknown>;
}

export interface PipelineStep {
  id: string;
  label: string;
  status: StepStatus;
  detail: string;
}

export interface LatestPatch {
  strategyId?: string | null;
  patchSummary?: string;
  minimalityFlag?: string;
  confidenceScore?: number;
  refusalReason?: string | null;
  changedRegions?: Array<{
    start_line: number;
    end_line: number;
    original_snippet: string;
    updated_snippet: string;
  }>;
  updatedCode?: string;
  patchDiff?: string;
  patchPath?: string | null;
  diffPath?: string | null;
}

export interface PatchAttempt {
  attemptIndex: number;
  strategyId?: string | null;
  patchSummary?: string;
  minimalityFlag?: string;
  confidenceScore?: number;
  refusalReason?: string | null;
  patchPath?: string | null;
  diffPath?: string | null;
  patchCode?: string;
  diffText?: string;
}

export interface VerifierPayload {
  decision: string;
  rationale: string;
  regressionFlags: string[];
  behaviorMatchStatus: string;
  originalFailureResolved: boolean;
  uncertaintyNotes: string;
  targetedFeedbackForRetry: string[];
}

export interface SessionArtifacts {
  sessionDir?: string | null;
  summaryPath?: string | null;
  tracePath?: string | null;
  stateSnapshotPath?: string | null;
  finalPatchPath?: string | null;
  failureSummaryPath?: string | null;
  intermediatePatchPaths?: string[];
  inputCodePath?: string | null;
}

export interface SessionPayload {
  session: {
    sessionId: string;
    status: string;
    finalDecision: string;
    finalMessage: string;
    targetFile: string;
    sessionDir: string;
    attemptsUsed: number;
    maxAttempts: number;
    behaviorMatchStatus: string;
    handoffCount: number;
    startedAt: string;
  };
  overview: {
    title: string;
    subtitle: string;
    targetUser: string;
    whyAgentic: string;
    scopedBoundaries: string[];
  };
  originalCode: string;
  originalExecution?: Record<string, unknown>;
  latestDiagnosis?: Record<string, unknown> | null;
  latestPatch?: LatestPatch | null;
  patchAttempts: PatchAttempt[];
  verifier: VerifierPayload;
  traceEvents: TraceEvent[];
  pipeline: PipelineStep[];
  artifacts: SessionArtifacts;
  summaryMarkdown: string;
  failureSummaryMarkdown: string;
  finalPatchedCode: string;
  sessionDirExists: boolean;
}

export interface EvaluationRow {
  case_id: string;
  case_type: string;
  input_or_scenario: string;
  expected_behavior: string;
  ideal_system_action: string;
  judgment_rule: string;
  task_success?: string;
  outcome_label?: string;
  retry_count?: string;
  latency_ms?: string;
  patch_breadth?: string;
  original_failure_resolved?: string;
  behavior_match_status?: string;
  evidence_or_citation?: string;
  notes?: string;
}

export interface EvaluationSnapshot {
  latestRunPath: string | null;
  summary: {
    totalCases: number;
    accepted: number;
    failedOrStopped: number;
    escalated: number;
    averageRetries: number;
    averageLatencyMs: number;
  } | null;
  results: EvaluationRow[];
  failureCases: EvaluationRow[];
  plannedRows: EvaluationRow[];
}
