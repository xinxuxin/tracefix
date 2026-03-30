import { motion } from "framer-motion";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { fetchCases, fetchEvaluation, fetchLatestSession, runDebugSession } from "./api";
import type {
  CaseItem,
  EvaluationRow,
  EvaluationSnapshot,
  PatchAttempt,
  PipelineStep,
  SessionPayload,
  StepStatus,
  TraceEvent,
} from "./types";

const FALLBACK_PIPELINE: PipelineStep[] = [
  { id: "controller", label: "Controller", status: "idle", detail: "Waiting for a run." },
  { id: "executor", label: "Executor", status: "idle", detail: "Bounded execution evidence." },
  { id: "diagnoser", label: "Diagnoser", status: "idle", detail: "Localized failure hypothesis." },
  { id: "patcher", label: "Patcher", status: "idle", detail: "Smallest reasonable edit." },
  { id: "verifier", label: "Verifier", status: "idle", detail: "Acceptance, retry, or stop." },
];

const FAILURE_NOTES: Record<
  string,
  {
    title: string;
    why: string;
    boundary: string;
  }
> = {
  bug_case_06_failure_superficial_fix: {
    title: "Superficial Fix Rejected",
    why: "The patch can remove the immediate crash, but the output still fails the intended greeting behavior check.",
    boundary: "The verifier refuses false-positive acceptance when expected output proves the patch is still behaviorally wrong.",
  },
  bug_case_07_failure_ambiguous_behavior: {
    title: "Ambiguous Success Escalated",
    why: "A localized rename can make the script run, but no explicit oracle shows that the behavior is truly correct.",
    boundary: "TraceFix stays conservative and escalates instead of claiming success without enough evidence.",
  },
};

const sectionMotion = {
  initial: { opacity: 0, y: 18 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.2 },
  transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] as const },
};

function App() {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [evaluation, setEvaluation] = useState<EvaluationSnapshot | null>(null);
  const [session, setSession] = useState<SessionPayload | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState<string>("");
  const [code, setCode] = useState<string>("");
  const [expectedOutput, setExpectedOutput] = useState<string>("");
  const [maxRetries, setMaxRetries] = useState<number>(2);
  const [loading, setLoading] = useState<boolean>(false);
  const [liveStepIndex, setLiveStepIndex] = useState<number>(0);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [caseItems, latestSession, evaluationSnapshot] = await Promise.all([
          fetchCases(),
          fetchLatestSession(),
          fetchEvaluation(),
        ]);
        if (cancelled) {
          return;
        }
        setCases(caseItems);
        setEvaluation(evaluationSnapshot);
        if (latestSession) {
          setSession(latestSession);
        }
        const preferred = caseItems.find((item) => item.caseId === "bug_case_02_name_error") ?? caseItems[0];
        if (preferred) {
          setSelectedCaseId(preferred.caseId);
          setCode(preferred.code);
          setExpectedOutput(preferred.expectedOutput ?? "");
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load frontend data.");
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!loading) {
      return;
    }
    const interval = window.setInterval(() => {
      setLiveStepIndex((index) => (index + 1) % FALLBACK_PIPELINE.length);
    }, 650);
    return () => window.clearInterval(interval);
  }, [loading]);

  const pipeline = useMemo(() => {
    if (loading) {
      return FALLBACK_PIPELINE.map((step, index) => ({
        ...step,
        status: index === liveStepIndex ? ("running" as StepStatus) : index < liveStepIndex ? ("success" as StepStatus) : "idle",
      }));
    }
    return session?.pipeline ?? FALLBACK_PIPELINE;
  }, [loading, liveStepIndex, session]);

  const evaluationRows = evaluation?.results.length ? evaluation.results : evaluation?.plannedRows ?? [];
  const evaluationSummary = useMemo(() => {
    if (evaluation?.summary) {
      return evaluation.summary;
    }
    const planned = evaluation?.plannedRows ?? [];
    return {
      totalCases: planned.length,
      accepted: planned.filter((row) => row.ideal_system_action === "accept").length,
      failedOrStopped: planned.filter((row) => row.ideal_system_action === "stop").length,
      escalated: planned.filter((row) => row.ideal_system_action === "escalate").length,
      averageRetries: 0,
      averageLatencyMs: 0,
    };
  }, [evaluation]);

  const groupedCases = useMemo(() => {
    return {
      happy_path: cases.filter((item) => item.group === "happy_path"),
      governance: cases.filter((item) => item.group === "governance"),
      failure_case: cases.filter((item) => item.group === "failure_case"),
    };
  }, [cases]);

  const failureHighlights = useMemo(() => {
    return Object.entries(FAILURE_NOTES).map(([caseId, note]) => {
      const caseInfo = cases.find((item) => item.caseId === caseId);
      const runRow = evaluationRows.find((row) => row.case_id === caseId);
      return {
        caseId,
        title: note.title,
        why: note.why,
        boundary: note.boundary,
        caseInfo,
        outcome: runRow?.outcome_label ?? runRow?.ideal_system_action ?? "planned",
      };
    });
  }, [cases, evaluationRows]);

  async function handleRun() {
    setLoading(true);
    setError("");
    try {
      const activeCase = cases.find((item) => item.caseId === selectedCaseId);
      const result = await runDebugSession({
        code,
        filename: activeCase?.filename ?? "workspace_case.py",
        expectedOutput: expectedOutput.trim() ? expectedOutput : null,
        maxRetries,
      });
      setSession(result);
      const latestEvaluation = await fetchEvaluation().catch(() => null);
      if (latestEvaluation) {
        setEvaluation(latestEvaluation);
      }
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "TraceFix run failed.");
    } finally {
      setLoading(false);
      setLiveStepIndex(0);
    }
  }

  function loadCase(caseItem: CaseItem) {
    setSelectedCaseId(caseItem.caseId);
    setCode(caseItem.code);
    setExpectedOutput(caseItem.expectedOutput ?? "");
    setError("");
  }

  const latestPatch = session?.latestPatch;

  return (
    <div className="min-h-screen bg-hero-wash px-4 py-6 text-slate-900 sm:px-6 lg:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <motion.header
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] as const }}
          className="overflow-hidden rounded-[32px] border border-white/70 bg-white/85 p-8 shadow-panel backdrop-blur"
        >
          <div className="grid gap-8 lg:grid-cols-[1.35fr_0.9fr]">
            <div className="space-y-5">
              <div className="inline-flex items-center rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-teal-800">
                Optional Local Visual Layer
              </div>
              <div className="space-y-3">
                <p className="font-display text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                  TraceFix Visual Frontend
                </p>
                <p className="max-w-3xl text-lg leading-8 text-slate-700">
                  A polished local demo surface for the existing CLI-first TraceFix workflow, designed to show
                  component handoffs, evidence traces, patch diffs, verifier decisions, and evaluation outcomes without
                  changing the underlying debugging scope.
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <StatCard
                  label="Target User"
                  value="Beginner-to-intermediate Python learners"
                  tone="teal"
                />
                <StatCard
                  label="Why Agentic"
                  value="Evidence, diagnosis, patching, and verification are separate roles with bounded retries."
                  tone="amber"
                />
              </div>
            </div>
            <div className="grid gap-3 rounded-[28px] border border-slate-200/80 bg-slate-50/80 p-5">
              <MiniInfo title="Architecture Summary">
                Controller coordinates Executor, Diagnoser, Patcher, and Verifier while persisting traces and session state.
              </MiniInfo>
              <MiniInfo title="Scoped Boundaries">
                Single-file Python only, no internet, no package installation during debugging, no multi-file reasoning.
              </MiniInfo>
              <MiniInfo title="Why This View Helps">
                It turns existing artifacts into screenshot-ready evidence for the final report and a short demo video.
              </MiniInfo>
            </div>
          </div>
        </motion.header>

        {error ? (
          <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
        ) : null}

        <motion.section {...sectionMotion} className="panel-grid lg:grid-cols-[1.18fr_0.82fr]">
          <Panel
            eyebrow="Debug Workspace"
            title="Run TraceFix on pasted code or a sample case"
            subtitle="This remains a thin presentation layer. The run still goes through the existing controller and saves normal session artifacts."
          >
            <div className="grid gap-4">
              <label className="grid gap-2 text-sm font-medium text-slate-700">
                Sample Case
                <select
                  value={selectedCaseId}
                  onChange={(event) => {
                    const chosen = cases.find((item) => item.caseId === event.target.value);
                    if (chosen) {
                      loadCase(chosen);
                    }
                  }}
                  className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-200"
                >
                  <option value="">Select a sample case</option>
                  {cases.map((caseItem) => (
                    <option key={caseItem.caseId} value={caseItem.caseId}>
                      {caseItem.title}
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-2 text-sm font-medium text-slate-700">
                Python Code
                <textarea
                  value={code}
                  onChange={(event) => setCode(event.target.value)}
                  spellCheck={false}
                  className="min-h-[280px] rounded-[24px] border border-slate-300 bg-slate-950 px-4 py-4 font-mono text-sm text-slate-100 shadow-inner outline-none transition focus:border-teal-400 focus:ring-2 focus:ring-teal-200"
                />
              </label>

              <div className="grid gap-4 md:grid-cols-[1fr_180px]">
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Expected Output
                  <textarea
                    value={expectedOutput}
                    onChange={(event) => setExpectedOutput(event.target.value)}
                    placeholder="Optional verifier oracle"
                    spellCheck={false}
                    className="min-h-[100px] rounded-2xl border border-slate-300 bg-white px-4 py-3 font-mono text-sm shadow-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-200"
                  />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Max Retries
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={maxRetries}
                    onChange={(event) => setMaxRetries(Number(event.target.value) || 1)}
                    className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-200"
                  />
                </label>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => void handleRun()}
                  disabled={loading || !code.trim()}
                  className="rounded-full bg-teal-700 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-teal-700/20 transition hover:bg-teal-600 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {loading ? "Running TraceFix..." : "Run TraceFix"}
                </button>
                <span className="text-sm text-slate-500">
                  {session
                    ? `Latest session: ${session.session.sessionId}`
                    : "Load a sample or paste a script to create a new local session."}
                </span>
              </div>
            </div>
          </Panel>

          <Panel
            eyebrow="Animated Pipeline"
            title="Component handoffs"
            subtitle="Status colors and motion make the orchestration path easier to explain in a demo."
          >
            <div className="space-y-4">
              <div className="grid gap-3">
                {pipeline.map((step, index) => (
                  <motion.div
                    key={step.id}
                    layout
                    animate={{
                      scale: loading && index === liveStepIndex ? 1.02 : 1,
                      borderColor: step.status === "running" ? "rgba(15,118,110,0.4)" : "rgba(226,232,240,1)",
                    }}
                    className="rounded-[22px] border bg-slate-50 px-4 py-4 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-display text-lg font-semibold text-slate-900">{step.label}</div>
                        <div className="mt-1 text-sm leading-6 text-slate-600">{step.detail}</div>
                      </div>
                      <StatusPill status={step.status} />
                    </div>
                  </motion.div>
                ))}
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <MetricCard label="Attempts" value={String(session?.session.attemptsUsed ?? 0)} />
                <MetricCard label="Final Decision" value={session?.session.finalDecision ?? "n/a"} />
                <MetricCard label="Handoffs" value={String(session?.session.handoffCount ?? 0)} />
              </div>
            </div>
          </Panel>
        </motion.section>

        <motion.section {...sectionMotion} className="panel-grid lg:grid-cols-[0.95fr_1.05fr]">
          <Panel
            eyebrow="Sample Cases"
            title="Demo-ready case library"
            subtitle="Load a case into the workspace with one click. The groups mirror the current evaluation and failure-analysis framing."
          >
            <div className="space-y-5">
              <CaseGroup title="Happy-path demos" cases={groupedCases.happy_path} onLoad={loadCase} activeCaseId={selectedCaseId} />
              <CaseGroup title="Governance demos" cases={groupedCases.governance} onLoad={loadCase} activeCaseId={selectedCaseId} />
              <CaseGroup title="Failure / stop demos" cases={groupedCases.failure_case} onLoad={loadCase} activeCaseId={selectedCaseId} />
            </div>
          </Panel>

          <Panel
            eyebrow="Verification Result"
            title="Final verifier decision"
            subtitle="This panel is intentionally decision-centric because the course report needs to show acceptance, retry, escalation, and stop behavior."
          >
            <div className="grid gap-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <VerifierMetric label="Decision" value={session?.verifier.decision ?? "not_run"} tone="primary" />
                <VerifierMetric
                  label="Original Failure Resolved"
                  value={session ? (session.verifier.originalFailureResolved ? "yes" : "no") : "unknown"}
                />
                <VerifierMetric
                  label="Behavior Match"
                  value={session?.verifier.behaviorMatchStatus ?? "unknown"}
                />
                <VerifierMetric label="Retry Count" value={String(session?.session.attemptsUsed ?? 0)} />
              </div>
              <InfoBlock title="Rationale">
                {session?.verifier.rationale ?? "Run a session to view final verifier reasoning."}
              </InfoBlock>
              <InfoBlock title="Uncertainty Notes">
                {session?.verifier.uncertaintyNotes ?? "No uncertainty notes yet."}
              </InfoBlock>
              <TagList
                title="Regression Flags"
                values={session?.verifier.regressionFlags ?? []}
                emptyLabel="No regression flags recorded."
              />
              <TagList
                title="Retry Feedback"
                values={session?.verifier.targetedFeedbackForRetry ?? []}
                emptyLabel="No retry feedback for this session."
              />
            </div>
          </Panel>
        </motion.section>

        <motion.section {...sectionMotion} className="panel-grid lg:grid-cols-[1.1fr_0.9fr]">
          <Panel
            eyebrow="Trace Timeline"
            title="Inspectable handoff sequence"
            subtitle="The timeline surfaces the JSONL trace as a readable audit trail for screenshots and walkthroughs."
          >
            <div className="space-y-3">
              {session?.traceEvents.length ? (
                session.traceEvents.map((event, index) => (
                  <details
                    key={`${event.timestamp ?? "event"}-${index}`}
                    className="rounded-[22px] border border-slate-200 bg-slate-50 px-4 py-3"
                  >
                    <summary className="cursor-pointer list-none">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
                            #{index + 1} {event.timestamp ?? "no timestamp"}
                          </div>
                          <div className="mt-1 font-medium text-slate-900">
                            {event.handoff ?? event.event ?? "trace_event"}
                          </div>
                          <div className="mt-1 text-sm text-slate-600">{event.summary ?? "No summary"}</div>
                        </div>
                        <div className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm">
                          attempt {event.attempt_index ?? 0}
                        </div>
                      </div>
                    </summary>
                    <pre className="code-scroll mt-3 overflow-x-auto rounded-2xl bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                      {JSON.stringify(event.payload ?? {}, null, 2)}
                    </pre>
                  </details>
                ))
              ) : (
                <EmptyState text="No trace loaded yet. Run a case to populate the handoff timeline." />
              )}
            </div>
          </Panel>

          <Panel
            eyebrow="Session Artifacts"
            title="Saved outputs for the report"
            subtitle="These are the same local artifacts already produced by the controller; the frontend only surfaces them."
          >
            <div className="space-y-3">
              <ArtifactRow label="Session folder" value={session?.artifacts.sessionDir} />
              <ArtifactRow label="Summary" value={session?.artifacts.summaryPath} />
              <ArtifactRow label="Trace JSONL" value={session?.artifacts.tracePath} />
              <ArtifactRow label="State snapshot" value={session?.artifacts.stateSnapshotPath} />
              <ArtifactRow label="Input copy" value={session?.artifacts.inputCodePath} />
              <ArtifactRow label="Final patch" value={session?.artifacts.finalPatchPath} />
              <ArtifactRow label="Failure summary" value={session?.artifacts.failureSummaryPath} />
              <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Summary Preview</div>
                <pre className="code-scroll mt-3 max-h-52 overflow-auto whitespace-pre-wrap font-mono text-xs leading-6 text-slate-700">
                  {session?.summaryMarkdown || session?.failureSummaryMarkdown || "No saved markdown preview available yet."}
                </pre>
              </div>
            </div>
          </Panel>
        </motion.section>

        <motion.section {...sectionMotion}>
          <Panel
            eyebrow="Patch Diff"
            title="Original vs patched code"
            subtitle="The diff view stays focused on the latest bounded patch so reviewers can see exactly what changed."
          >
            {latestPatch ? (
              <div className="grid gap-5 lg:grid-cols-2">
                <div className="grid gap-3">
                  <PatchHeader
                    summary={latestPatch.patchSummary ?? "Latest patch"}
                    breadth={latestPatch.minimalityFlag}
                    strategy={latestPatch.strategyId}
                  />
                  <CodePanel title="Original Code" code={session?.originalCode ?? ""} />
                </div>
                <div className="grid gap-3">
                  <PatchHeader
                    summary={latestPatch.refusalReason ? "Patch refused" : "Patched Code"}
                    breadth={latestPatch.minimalityFlag}
                    strategy={latestPatch.strategyId}
                  />
                  <CodePanel title="Updated Code" code={latestPatch.updatedCode || session?.finalPatchedCode || ""} />
                </div>
                <div className="lg:col-span-2">
                  <DiffPanel diffText={latestPatch.patchDiff ?? ""} />
                </div>
              </div>
            ) : (
              <EmptyState text="No patch artifact exists for the current session. This usually means the patcher refused or the script already succeeded." />
            )}
          </Panel>
        </motion.section>

        <motion.section {...sectionMotion} className="panel-grid lg:grid-cols-[1fr_1fr]">
          <Panel
            eyebrow="Evaluation Dashboard"
            title="Current evaluation snapshot"
            subtitle="If a real evaluation run exists, metrics come from the latest CSV. Otherwise the dashboard falls back to the planned course cases."
          >
            <div className="grid gap-4">
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <MetricCard label="Total Cases" value={String(evaluationSummary.totalCases)} />
                <MetricCard label="Accepted" value={String(evaluationSummary.accepted)} />
                <MetricCard label="Failed or Stopped" value={String(evaluationSummary.failedOrStopped)} />
                <MetricCard label="Escalated" value={String(evaluationSummary.escalated)} />
                <MetricCard label="Avg Retries" value={String(evaluationSummary.averageRetries)} />
                <MetricCard label="Avg Latency (ms)" value={String(evaluationSummary.averageLatencyMs)} />
              </div>
              <div className="overflow-hidden rounded-[24px] border border-slate-200">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                    <thead className="bg-slate-50 text-slate-500">
                      <tr>
                        <TableHead>Case</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Outcome</TableHead>
                        <TableHead>Retries</TableHead>
                        <TableHead>Behavior</TableHead>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {evaluationRows.map((row) => (
                        <tr key={row.case_id}>
                          <TableCell>{row.case_id}</TableCell>
                          <TableCell>{row.case_type}</TableCell>
                          <TableCell>{row.outcome_label ?? row.ideal_system_action}</TableCell>
                          <TableCell>{row.retry_count ?? "planned"}</TableCell>
                          <TableCell>{row.behavior_match_status ?? row.expected_behavior}</TableCell>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="text-sm text-slate-500">
                {evaluation?.latestRunPath
                  ? `Latest evaluation run: ${evaluation.latestRunPath}`
                  : "No saved evaluation run found yet. Planned case metadata is shown as a fallback."}
              </div>
            </div>
          </Panel>

          <Panel
            eyebrow="Failure Analysis"
            title="Two failure cases worth highlighting"
            subtitle="These are the best screenshots for showing that TraceFix is conservative, not over-claiming."
          >
            <div className="grid gap-4">
              {failureHighlights.map((item) => (
                <div key={item.caseId} className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="font-display text-lg font-semibold text-slate-900">{item.title}</div>
                      <div className="mt-1 text-sm text-slate-500">
                        {item.caseInfo?.caseId ?? item.caseId} • current outcome: {item.outcome}
                      </div>
                    </div>
                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                      Failure analysis candidate
                    </span>
                  </div>
                  <div className="mt-4 grid gap-3 text-sm leading-6 text-slate-700">
                    <p><span className="font-semibold text-slate-900">What happened:</span> {item.why}</p>
                    <p><span className="font-semibold text-slate-900">Why verifier did not accept:</span> {item.boundary}</p>
                    <p><span className="font-semibold text-slate-900">Why this is useful in the report:</span> It shows the boundary between bounded automation and human judgment.</p>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </motion.section>

        <motion.section {...sectionMotion}>
          <Panel
            eyebrow="Patch Attempts"
            title="Intermediate patch versions"
            subtitle="When a session retries, the frontend keeps those attempts visible instead of only showing the final answer."
          >
            <div className="space-y-3">
              {session?.patchAttempts.length ? (
                session.patchAttempts.map((attempt: PatchAttempt) => (
                  <details key={attempt.attemptIndex} className="rounded-[22px] border border-slate-200 bg-slate-50 px-4 py-3">
                    <summary className="cursor-pointer list-none">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <div className="font-medium text-slate-900">Attempt {attempt.attemptIndex}</div>
                          <div className="mt-1 text-sm text-slate-600">{attempt.patchSummary ?? "No patch summary"}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          {attempt.minimalityFlag ? (
                            <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 shadow-sm">
                              {attempt.minimalityFlag}
                            </span>
                          ) : null}
                          {attempt.strategyId ? (
                            <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800">
                              {attempt.strategyId}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </summary>
                    <div className="mt-3 grid gap-4 lg:grid-cols-2">
                      <CodePanel title="Patch Candidate" code={attempt.patchCode ?? ""} />
                      <DiffPanel diffText={attempt.diffText ?? ""} compact />
                    </div>
                  </details>
                ))
              ) : (
                <EmptyState text="No intermediate patch attempts are available yet." />
              )}
            </div>
          </Panel>
        </motion.section>
      </div>
    </div>
  );
}

function Panel(props: { eyebrow: string; title: string; subtitle: string; children: ReactNode }) {
  return (
    <section className="rounded-[30px] border border-white/70 bg-white/88 p-6 shadow-panel backdrop-blur">
      <div className="mb-5 space-y-2">
        <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">{props.eyebrow}</div>
        <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950">{props.title}</h2>
        <p className="max-w-3xl text-sm leading-7 text-slate-600">{props.subtitle}</p>
      </div>
      {props.children}
    </section>
  );
}

function StatCard(props: { label: string; value: string; tone?: "teal" | "amber" }) {
  const toneClasses =
    props.tone === "amber"
      ? "border-amber-200 bg-amber-50 text-amber-900"
      : "border-teal-200 bg-teal-50 text-teal-900";
  return (
    <div className={`rounded-[24px] border px-4 py-4 ${toneClasses}`}>
      <div className="text-xs font-semibold uppercase tracking-[0.18em] opacity-70">{props.label}</div>
      <div className="mt-2 text-sm leading-6">{props.value}</div>
    </div>
  );
}

function MiniInfo(props: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-[22px] border border-white/80 bg-white/80 p-4 shadow-sm">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{props.title}</div>
      <div className="mt-2 text-sm leading-6 text-slate-700">{props.children}</div>
    </div>
  );
}

function StatusPill({ status }: { status: StepStatus }) {
  const styles: Record<StepStatus, string> = {
    idle: "bg-slate-100 text-slate-600",
    running: "bg-teal-100 text-teal-800",
    success: "bg-emerald-100 text-emerald-800",
    retry: "bg-amber-100 text-amber-800",
    failure: "bg-rose-100 text-rose-800",
    escalated: "bg-orange-100 text-orange-800",
    stopped: "bg-slate-200 text-slate-700",
  };
  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${styles[status]}`}>{status}</span>;
}

function MetricCard(props: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{props.label}</div>
      <div className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{props.value}</div>
    </div>
  );
}

function VerifierMetric(props: { label: string; value: string; tone?: "primary" }) {
  return (
    <div className={`rounded-[22px] border p-4 ${props.tone === "primary" ? "border-teal-200 bg-teal-50" : "border-slate-200 bg-slate-50"}`}>
      <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{props.label}</div>
      <div className="mt-2 text-lg font-semibold text-slate-950">{props.value}</div>
    </div>
  );
}

function InfoBlock(props: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{props.title}</div>
      <div className="mt-2 text-sm leading-7 text-slate-700">{props.children}</div>
    </div>
  );
}

function TagList(props: { title: string; values: string[]; emptyLabel: string }) {
  return (
    <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{props.title}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {props.values.length ? (
          props.values.map((value) => (
            <span key={value} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 shadow-sm">
              {value}
            </span>
          ))
        ) : (
          <span className="text-sm text-slate-500">{props.emptyLabel}</span>
        )}
      </div>
    </div>
  );
}

function CaseGroup(props: {
  title: string;
  cases: CaseItem[];
  onLoad: (caseItem: CaseItem) => void;
  activeCaseId: string;
}) {
  return (
    <div className="space-y-3">
      <div className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">{props.title}</div>
      <div className="grid gap-3">
        {props.cases.map((caseItem) => {
          const active = props.activeCaseId === caseItem.caseId;
          return (
            <button
              key={caseItem.caseId}
              type="button"
              onClick={() => props.onLoad(caseItem)}
              className={`rounded-[22px] border p-4 text-left transition ${
                active
                  ? "border-teal-300 bg-teal-50 shadow-sm"
                  : "border-slate-200 bg-slate-50 hover:border-slate-300 hover:bg-white"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-display text-lg font-semibold text-slate-900">{caseItem.title}</div>
                  <div className="mt-1 text-sm leading-6 text-slate-600">{caseItem.description}</div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 shadow-sm">
                    {caseItem.badge}
                  </span>
                  {caseItem.recommendedForVideo ? (
                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                      Video-ready
                    </span>
                  ) : null}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ArtifactRow(props: { label: string; value?: string | null }) {
  return (
    <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{props.label}</div>
      <div className="mt-2 break-all font-mono text-xs leading-6 text-slate-700">{props.value ?? "Not available"}</div>
    </div>
  );
}

function PatchHeader(props: { summary: string; breadth?: string; strategy?: string | null }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div>
        <div className="font-medium text-slate-900">{props.summary}</div>
        <div className="mt-1 text-sm text-slate-600">Strategy: {props.strategy ?? "n/a"}</div>
      </div>
      <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 shadow-sm">
        {props.breadth ?? "no diff"}
      </span>
    </div>
  );
}

function CodePanel(props: { title: string; code: string }) {
  return (
    <div className="overflow-hidden rounded-[22px] border border-slate-200 bg-slate-950">
      <div className="border-b border-slate-800 px-4 py-3 text-xs uppercase tracking-[0.18em] text-slate-400">
        {props.title}
      </div>
      <pre className="code-scroll max-h-[360px] overflow-auto whitespace-pre-wrap p-4 font-mono text-xs leading-6 text-slate-100">
        {props.code || "No code available."}
      </pre>
    </div>
  );
}

function DiffPanel(props: { diffText: string; compact?: boolean }) {
  if (!props.diffText) {
    return <EmptyState text="No unified diff available for this patch." />;
  }
  return (
    <div className="overflow-hidden rounded-[22px] border border-slate-200 bg-slate-950">
      <div className="border-b border-slate-800 px-4 py-3 text-xs uppercase tracking-[0.18em] text-slate-400">
        Unified Diff
      </div>
      <pre className={`code-scroll overflow-auto whitespace-pre-wrap font-mono text-xs leading-6 ${props.compact ? "max-h-[240px]" : "max-h-[360px]"} p-4`}>
        {props.diffText.split("\n").map((line, index) => (
          <div
            key={`${line}-${index}`}
            className={
              line.startsWith("+")
                ? "text-emerald-300"
                : line.startsWith("-")
                  ? "text-rose-300"
                  : line.startsWith("@@")
                    ? "text-amber-300"
                    : "text-slate-200"
            }
          >
            {line || " "}
          </div>
        ))}
      </pre>
    </div>
  );
}

function EmptyState(props: { text: string }) {
  return (
    <div className="rounded-[22px] border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
      {props.text}
    </div>
  );
}

function TableHead(props: { children: ReactNode }) {
  return <th className="px-4 py-3 font-semibold">{props.children}</th>;
}

function TableCell(props: { children: ReactNode }) {
  return <td className="px-4 py-3 align-top text-slate-700">{props.children}</td>;
}

export default App;
