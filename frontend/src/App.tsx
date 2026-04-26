import { AnimatePresence, motion } from "framer-motion";
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
  { id: "controller", label: "Controller", status: "idle", detail: "Owns session state and orchestration." },
  { id: "executor", label: "Executor", status: "idle", detail: "Runs bounded local Python execution." },
  { id: "diagnoser", label: "Diagnoser", status: "idle", detail: "Produces evidence-grounded repair hypotheses." },
  { id: "patcher", label: "Patcher", status: "idle", detail: "Synthesizes the smallest reasonable edit." },
  { id: "verifier", label: "Verifier", status: "idle", detail: "Accepts, retries, escalates, or stops." },
];

const FAILURE_NOTES: Record<
  string,
  {
    title: string;
    why: string;
    boundary: string;
    futureFix: string;
  }
> = {
  bug_case_06_failure_superficial_fix: {
    title: "Superficial Fix Rejected",
    why: "The patch can remove the immediate crash, but the output still fails the intended greeting behavior check.",
    boundary: "The verifier refuses false-positive acceptance when expected output proves the patch is still behaviorally wrong.",
    futureFix: "Add stronger behavior-level patch evaluation or richer test oracles for greeting-format cases.",
  },
  bug_case_07_failure_ambiguous_behavior: {
    title: "Ambiguous Success Escalated",
    why: "A localized rename can make the script run, but no explicit oracle shows that the behavior is truly correct.",
    boundary: "TraceFix stays conservative and escalates instead of claiming success without enough evidence.",
    futureFix: "Support richer lightweight behavior checks when expected output is unavailable but intent is partially known.",
  },
};

const sectionMotion = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.18 },
  transition: { duration: 0.42, ease: [0.22, 1, 0.36, 1] as const },
};

const chartColors = {
  accept: "bg-emerald-500",
  stop: "bg-rose-500",
  escalate: "bg-violet-500",
  retry: "bg-cyan-500",
  planned: "bg-slate-400",
};

type ExplorerTab = "trace" | "diff" | "attempts" | "artifacts";
type DiffView = "split" | "unified";
type ArtifactPreview = "summary" | "failure" | "paths";

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
  const [copiedKey, setCopiedKey] = useState<string>("");
  const [traceFilter, setTraceFilter] = useState<string>("all");
  const [explorerTab, setExplorerTab] = useState<ExplorerTab>("trace");
  const [diffView, setDiffView] = useState<DiffView>("split");
  const [artifactPreview, setArtifactPreview] = useState<ArtifactPreview>("summary");
  const [selectedAttemptIndex, setSelectedAttemptIndex] = useState<number>(0);
  const [selectedCaseGroup, setSelectedCaseGroup] = useState<CaseItem["group"]>("happy_path");

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
          setSelectedCaseGroup(preferred.group);
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
    }, 620);
    return () => window.clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    if (!session) {
      return;
    }
    setTraceFilter("all");
    setSelectedAttemptIndex(Math.max(session.patchAttempts.length - 1, 0));
    setExplorerTab(session.latestPatch ? "diff" : "trace");
    setArtifactPreview(session.failureSummaryMarkdown ? "failure" : "summary");
  }, [session]);

  useEffect(() => {
    if (!copiedKey) {
      return;
    }
    const timeout = window.setTimeout(() => setCopiedKey(""), 1200);
    return () => window.clearTimeout(timeout);
  }, [copiedKey]);

  const selectedCase = useMemo(
    () => cases.find((item) => item.caseId === selectedCaseId) ?? null,
    [cases, selectedCaseId],
  );

  const pipeline = useMemo(() => {
    if (loading) {
      return FALLBACK_PIPELINE.map((step, index) => ({
        ...step,
        status:
          index === liveStepIndex
            ? ("running" as StepStatus)
            : index < liveStepIndex
              ? ("success" as StepStatus)
              : ("idle" as StepStatus),
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

  const groupedCases = useMemo(
    () => ({
      happy_path: cases.filter((item) => item.group === "happy_path"),
      governance: cases.filter((item) => item.group === "governance"),
      failure_case: cases.filter((item) => item.group === "failure_case"),
    }),
    [cases],
  );

  const visibleCaseGroups = useMemo(
    () => ({
      label:
        selectedCaseGroup === "happy_path"
          ? "Happy-path demos"
          : selectedCaseGroup === "governance"
            ? "Governance demos"
            : "Failure / stop demos",
      cases: groupedCases[selectedCaseGroup],
    }),
    [groupedCases, selectedCaseGroup],
  );

  const failureHighlights = useMemo(() => {
    return Object.entries(FAILURE_NOTES).map(([caseId, note]) => {
      const caseInfo = cases.find((item) => item.caseId === caseId);
      const runRow = evaluationRows.find((row) => row.case_id === caseId);
      return {
        caseId,
        title: note.title,
        why: note.why,
        boundary: note.boundary,
        futureFix: note.futureFix,
        caseInfo,
        outcome: runRow?.outcome_label ?? runRow?.ideal_system_action ?? "planned",
      };
    });
  }, [cases, evaluationRows]);

  const traceFilters = useMemo(() => {
    const labels = new Set<string>();
    for (const event of session?.traceEvents ?? []) {
      labels.add(getTraceComponent(event));
    }
    return ["all", ...Array.from(labels)];
  }, [session]);

  const filteredTraceEvents = useMemo(() => {
    const events = session?.traceEvents ?? [];
    if (traceFilter === "all") {
      return events;
    }
    return events.filter((event) => getTraceComponent(event) === traceFilter);
  }, [session, traceFilter]);

  const selectedAttempt = useMemo(() => {
    if (!session?.patchAttempts.length) {
      return null;
    }
    return session.patchAttempts[Math.min(selectedAttemptIndex, session.patchAttempts.length - 1)] ?? null;
  }, [selectedAttemptIndex, session]);

  const storySummary = useMemo(() => {
    const originalOutcome = stringifyRecordValue(session?.originalExecution, "outcome_label") ?? "not_run";
    const exceptionType = stringifyRecordValue(session?.originalExecution, "exception_type") ?? "unknown";
    return {
      initialFailure: `${originalOutcome} • ${exceptionType}`,
      diagnosis: stringifyRecordValue(session?.latestDiagnosis, "likely_root_cause") ?? "No diagnosis yet.",
      patch: session?.latestPatch?.patchSummary ?? "No patch candidate yet.",
      decision: session?.verifier.rationale ?? "Run a session to see the final decision trail.",
    };
  }, [session]);

  const evaluationDistribution = useMemo(() => {
    const total = Math.max(evaluationSummary.totalCases, 1);
    return [
      { label: "Accepted", value: evaluationSummary.accepted, key: "accept" as const },
      { label: "Stopped", value: evaluationSummary.failedOrStopped, key: "stop" as const },
      { label: "Escalated", value: evaluationSummary.escalated, key: "escalate" as const },
    ].map((item) => ({
      ...item,
      width: `${(item.value / total) * 100}%`,
    }));
  }, [evaluationSummary]);

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
    setSelectedCaseGroup(caseItem.group);
    setError("");
  }

  async function copyText(key: string, value: string | null | undefined) {
    if (!value) {
      return;
    }
    try {
      await navigator.clipboard.writeText(value);
      setCopiedKey(key);
    } catch {
      setError("Clipboard copy failed in this browser context.");
    }
  }

  const decisionTone = getDecisionTone(session?.verifier.decision ?? session?.session.finalDecision ?? "not_run");
  const heroMetrics = [
    {
      label: "Current Mode",
      value: loading ? "Running" : session?.session.finalDecision ?? "Ready",
      helper: loading ? "Simulating live pipeline progression" : "Latest session state",
    },
    {
      label: "Handoffs",
      value: String(session?.session.handoffCount ?? 0),
      helper: "Explicit traceable transitions between components",
    },
    {
      label: "Retries Used",
      value: String(session?.session.attemptsUsed ?? 0),
      helper: "Bounded retry budget remains visible",
    },
  ];

  const demoRunOfShow = [
    {
      time: "0:00-0:30",
      title: "Problem and target user",
      action: "Start at the hero and Demo Roadmap. Explain that TraceFix helps Python learners judge whether a patch restores behavior, not just whether a crash disappeared.",
    },
    {
      time: "0:30-1:10",
      title: "Architecture",
      action: "Point to the system strip and pipeline cards: Controller, Executor, Diagnoser, Patcher, Verifier, with session state and local artifacts.",
    },
    {
      time: "1:10-2:30",
      title: "Main workflow",
      action: "Use the workspace with bug_case_02_name_error.py, expected output 10.70, then click Run TraceFix and show the end-to-end flow.",
    },
    {
      time: "2:30-3:20",
      title: "Evidence layer",
      action: "Open Session Explorer tabs for trace timeline, patch diff, retry attempts, and artifacts. These are the source-of-truth evidence surfaces.",
    },
    {
      time: "3:20-4:20",
      title: "Boundary behavior",
      action: "Use Failure Analysis to show superficial-fix rejection and ambiguous/no-oracle escalation instead of false success.",
    },
    {
      time: "4:20-5:00",
      title: "Evaluation and final output",
      action: "End on Evaluation Dashboard and Final Output & Evidence Package to show seven cases, artifacts, limitations, and what to submit.",
    },
  ];

  const officialCoverage = [
    { requirement: "Problem and target user", location: "Hero + Demo Roadmap", status: "PASS" },
    { requirement: "Architecture", location: "System Strip + Pipeline View", status: "PASS" },
    { requirement: "Main workflow beginning to end", location: "Debug Workspace + Pipeline + Verification", status: "PASS" },
    { requirement: "Coordination / branching / agent interaction", location: "Pipeline View + Trace Timeline + Retry Attempts", status: "PASS" },
    { requirement: "Evidence layer: logs, traces, outputs, artifacts", location: "Session Explorer tabs + Artifact cards", status: "PASS" },
    { requirement: "Failure, limitation, or boundary behavior", location: "Failure Analysis cards", status: "PASS" },
    { requirement: "Final output, artifact, or export", location: "Final Output & Evidence Package", status: "PASS" },
    { requirement: "Mostly actual project, not slides", location: "Interactive local frontend backed by API/artifacts", status: "PASS" },
  ];

  const finalEvidenceItems = [
    { label: "Latest evaluation run", value: evaluation?.latestRunPath ?? "evaluation/runs/20260425T180442Z" },
    { label: "Root evaluation CSV", value: "evaluation/evaluation_results.csv" },
    { label: "Failure log", value: "evaluation/failure_log.md" },
    { label: "Trace JSONL", value: session?.artifacts.tracePath ?? "Run a session to populate trace.jsonl" },
    { label: "Session state", value: session?.artifacts.stateSnapshotPath ?? "Run a session to populate session_state.json" },
    { label: "Final patch", value: session?.artifacts.finalPatchPath ?? "Accepted sessions save final_patched_script.py" },
    { label: "Final report draft", value: "docs/final_report_draft.md" },
    { label: "Submission checklist", value: "docs/phase3_submission_checklist.md" },
  ];

  return (
    <div className="min-h-screen bg-app-shell px-4 py-5 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-[1440px] flex-col gap-6">
        <TopBar decisionTone={decisionTone} session={session} />

        <motion.header
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.46, ease: [0.22, 1, 0.36, 1] }}
          className="overflow-hidden rounded-[32px] border border-slate-800/80 bg-slate-950 shadow-panel"
        >
          <div className="relative px-6 py-7 sm:px-8 lg:px-10">
            <div className="hero-mesh absolute inset-0 opacity-100" />
            <div className="hero-grid absolute inset-0 opacity-100" />
            <div className="relative grid gap-8 lg:grid-cols-[1.15fr_0.85fr]">
              <div className="space-y-6">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="inline-flex items-center rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-200">
                    Local Visual Demo Layer
                  </span>
                  <span className="inline-flex items-center rounded-full border border-violet-400/20 bg-violet-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-violet-200">
                    CLI-first bounded workflow preserved
                  </span>
                </div>

                <div className="max-w-4xl space-y-4">
                  <p className="font-display text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-[3.4rem]">
                    TraceFix Frontend
                  </p>
                  <p className="max-w-3xl text-base leading-8 text-slate-300 sm:text-lg">
                    A clearer, more technical demo surface for the existing TraceFix controller. It makes agent handoffs,
                    trace evidence, patch diffs, verifier decisions, and evaluation outcomes easy to inspect in a five-minute
                    walkthrough.
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  {heroMetrics.map((item, index) => (
                    <motion.div
                      key={item.label}
                      initial={{ opacity: 0, y: 14 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.08 * index, duration: 0.36 }}
                      className="rounded-[24px] border border-white/10 bg-white/5 p-4 backdrop-blur-sm"
                    >
                      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{item.label}</div>
                      <div className="mt-3 text-2xl font-semibold tracking-tight text-white">{item.value}</div>
                      <div className="mt-2 text-sm leading-6 text-slate-400">{item.helper}</div>
                    </motion.div>
                  ))}
                </div>

                <div className="flex flex-wrap gap-2">
                  {[
                    "Single-file Python only",
                    "Rules-first verifier",
                    "Bounded retries",
                    "Artifacts stay local",
                    "No internet during debugging",
                  ].map((item) => (
                    <span
                      key={item}
                      className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="grid gap-4">
                <div className="rounded-[28px] border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">System Strip</div>
                      <div className="mt-2 font-display text-xl font-semibold text-white">Execution to verification</div>
                    </div>
                    <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-semibold text-cyan-100">
                      Demo-friendly
                    </span>
                  </div>
                  <div className="mt-5 flex flex-col gap-3">
                    {FALLBACK_PIPELINE.map((step, index) => (
                      <div key={step.id} className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-slate-900/70 text-sm font-semibold text-white">
                          {index + 1}
                        </div>
                        <div className="flex-1 rounded-2xl border border-white/10 bg-slate-900/50 px-4 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <div>
                              <div className="font-medium text-white">{step.label}</div>
                              <div className="mt-1 text-sm text-slate-400">{step.detail}</div>
                            </div>
                            {index < FALLBACK_PIPELINE.length - 1 ? (
                              <div className="hidden h-px w-12 bg-gradient-to-r from-cyan-400/60 to-violet-400/60 lg:block" />
                            ) : null}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <MiniSignalCard label="Target User" value="Python learners" helper="One small script at a time" />
                  <MiniSignalCard
                    label="Why Agentic"
                    value="Separated responsibilities"
                    helper="Evidence, diagnosis, patching, verification"
                  />
                </div>
              </div>
            </div>
          </div>
        </motion.header>

        <StickySessionBar loading={loading} session={session} decisionTone={decisionTone} />

        <motion.section id="demo-roadmap" {...sectionMotion} className="panel-grid lg:grid-cols-[0.9fr_1.1fr]">
          <Panel
            eyebrow="Main Page Video Roadmap"
            title="Record the Phase 3 video from this page"
            subtitle="The main page now carries the official five-minute story: problem, architecture, workflow, evidence, boundary case, evaluation, and final artifacts."
          >
            <div className="grid gap-3">
              {demoRunOfShow.map((step, index) => (
                <DemoStepCard key={step.time} step={step} index={index} />
              ))}
            </div>
          </Panel>

          <Panel
            eyebrow="Official Requirement Coverage"
            title="Everything the video needs is visible on the main page"
            subtitle="Use this as a quick pre-recording checklist. It maps each official Phase 3 video requirement to an actual main-page section."
          >
            <div className="grid gap-3">
              {officialCoverage.map((item) => (
                <CoverageCard key={item.requirement} requirement={item.requirement} location={item.location} status={item.status} />
              ))}
            </div>
          </Panel>
        </motion.section>

        {error ? (
          <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 shadow-sm">
            {error}
          </div>
        ) : null}

        <motion.section id="workspace" {...sectionMotion} className="panel-grid lg:grid-cols-[1.08fr_0.92fr]">
          <Panel
            eyebrow="Debug Workspace"
            title="Start with a sample case or paste code"
            subtitle="The workspace is now more guided: load a case, review the optional behavior oracle, and run the existing controller flow without changing backend contracts."
          >
            <div className="grid gap-5">
              <div className="grid gap-4 md:grid-cols-[1fr_220px]">
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Sample case
                  <select
                    value={selectedCaseId}
                    onChange={(event) => {
                      const chosen = cases.find((item) => item.caseId === event.target.value);
                      if (chosen) {
                        loadCase(chosen);
                      }
                    }}
                    className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
                  >
                    <option value="">Select a sample case</option>
                    {cases.map((caseItem) => (
                      <option key={caseItem.caseId} value={caseItem.caseId}>
                        {caseItem.title}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Run Guidance</div>
                  <div className="mt-3 space-y-3 text-sm leading-6 text-slate-600">
                    <p>1. Load a sample case or paste your own single-file script.</p>
                    <p>2. Add expected output if you want stronger verifier evidence.</p>
                    <p>3. Run TraceFix, then inspect pipeline, trace, diff, and final decision.</p>
                  </div>
                </div>
              </div>

              <label className="grid gap-2 text-sm font-medium text-slate-700">
                Python code
                <div className="overflow-hidden rounded-[26px] border border-slate-800 bg-slate-950 shadow-lg shadow-slate-950/10">
                  <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
                      <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                      <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
                    </div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                      {selectedCase?.filename ?? "workspace_case.py"}
                    </div>
                  </div>
                  <textarea
                    value={code}
                    onChange={(event) => setCode(event.target.value)}
                    spellCheck={false}
                    className="min-h-[320px] w-full resize-y bg-slate-950 px-4 py-4 font-mono text-sm leading-7 text-slate-100 outline-none"
                  />
                </div>
              </label>

              <div className="grid gap-4 lg:grid-cols-[1fr_200px]">
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Expected output
                  <textarea
                    value={expectedOutput}
                    onChange={(event) => setExpectedOutput(event.target.value)}
                    placeholder="Optional verifier oracle. Leave blank to demonstrate escalation or uncertainty handling."
                    spellCheck={false}
                    className="min-h-[118px] rounded-2xl border border-slate-300 bg-white px-4 py-3 font-mono text-sm shadow-sm outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
                  />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Max retries
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={maxRetries}
                    onChange={(event) => setMaxRetries(Number(event.target.value) || 1)}
                    className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
                  />
                </label>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => void handleRun()}
                  disabled={loading || !code.trim()}
                  className="inline-flex items-center rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-slate-950/10 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {loading ? "Running TraceFix..." : "Run TraceFix"}
                </button>
                <button
                  type="button"
                  onClick={() => void copyText("workspace-code", code)}
                  className="rounded-full border border-slate-300 bg-white px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
                >
                  {copiedKey === "workspace-code" ? "Copied" : "Copy code"}
                </button>
                <span className="text-sm text-slate-500">
                  {session
                    ? `Latest session: ${session.session.sessionId}`
                    : "No active session yet. Load a case to begin the demo flow."}
                </span>
              </div>
            </div>
          </Panel>

          <Panel
            eyebrow="Sample Case Browser"
            title="Quick-load demo scenarios"
            subtitle="Grouped by happy path, governance, and failure analysis so it is obvious what to click first during a walkthrough."
          >
            <div className="grid gap-4">
              <SegmentedControl
                value={selectedCaseGroup}
                options={[
                  { value: "happy_path", label: "Happy path" },
                  { value: "governance", label: "Governance" },
                  { value: "failure_case", label: "Failure / stop" },
                ]}
                onChange={(value) => setSelectedCaseGroup(value as CaseItem["group"])}
              />

              <div className="grid gap-3">
                {visibleCaseGroups.cases.map((caseItem, index) => {
                  const active = selectedCaseId === caseItem.caseId;
                  return (
                    <motion.button
                      key={caseItem.caseId}
                      type="button"
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.04, duration: 0.28 }}
                      onClick={() => loadCase(caseItem)}
                      className={`rounded-[24px] border p-4 text-left transition ${
                        active
                          ? "border-cyan-400/70 bg-cyan-50 shadow-sm ring-2 ring-cyan-100"
                          : "border-slate-200 bg-slate-50 hover:border-slate-300 hover:bg-white"
                      }`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="space-y-2">
                          <div className="font-display text-lg font-semibold text-slate-950">{caseItem.title}</div>
                          <div className="text-sm leading-6 text-slate-600">{caseItem.description}</div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <CaseBadge group={caseItem.group} badge={caseItem.badge} />
                          {caseItem.recommendedForVideo ? (
                            <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-700">
                              Video-ready
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </motion.button>
                  );
                })}
              </div>

              <div className="rounded-[26px] border border-slate-200 bg-slate-50 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Case Preview</div>
                    <div className="mt-2 font-display text-xl font-semibold text-slate-950">
                      {selectedCase?.title ?? "Select a case"}
                    </div>
                    <div className="mt-2 text-sm leading-6 text-slate-600">
                      {selectedCase?.description ?? "Choose a sample case to inspect expected behavior and demo category."}
                    </div>
                  </div>
                  {selectedCase ? (
                    <button
                      type="button"
                      onClick={() => void copyText("case-path", selectedCase.path)}
                      className="rounded-full border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
                    >
                      {copiedKey === "case-path" ? "Copied path" : "Copy path"}
                    </button>
                  ) : null}
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <CaseInfo label="Expected output" value={selectedCase?.expectedOutput?.trim() || "No explicit oracle"} />
                  <CaseInfo
                    label="Best use"
                    value={selectedCase?.recommendedForVideo ? "Recommended in demo video" : "Useful supporting case"}
                  />
                </div>
              </div>
            </div>
          </Panel>
        </motion.section>

        <motion.section id="session-story" {...sectionMotion} className="panel-grid lg:grid-cols-[1.1fr_0.9fr]">
          <Panel
            eyebrow="Pipeline View"
            title="Component handoffs and retry path"
            subtitle="The pipeline is now directional and status-aware, so a viewer can understand where the session is currently active and how the final decision emerged."
          >
            <div className="grid gap-5">
              <PipelineVisualizer
                pipeline={pipeline}
                loading={loading}
                liveStepIndex={liveStepIndex}
                attemptsUsed={session?.session.attemptsUsed ?? 0}
                finalDecision={session?.session.finalDecision ?? "not_run"}
              />

              <div className="grid gap-3 md:grid-cols-4">
                <StoryCard label="Initial failure" value={storySummary.initialFailure} />
                <StoryCard label="Diagnoser conclusion" value={storySummary.diagnosis} />
                <StoryCard label="Patcher change" value={storySummary.patch} />
                <StoryCard label="Verifier decision" value={storySummary.decision} />
              </div>
            </div>
          </Panel>

          <Panel
            eyebrow="Verification Result"
            title="Final decision panel"
            subtitle="Structured for demo clarity: outcome first, evidence second, uncertainty and retry feedback immediately visible."
          >
            <div className="grid gap-4">
              <motion.div
                layout
                className={`rounded-[28px] border px-5 py-5 ${decisionTone.panelClass}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="text-[11px] font-semibold uppercase tracking-[0.22em] opacity-70">Final decision</div>
                    <div className="mt-2 font-display text-3xl font-semibold tracking-tight">
                      {session?.verifier.decision ?? "not_run"}
                    </div>
                    <div className="mt-3 max-w-2xl text-sm leading-7">
                      {session?.verifier.rationale ?? "Run a session to populate final verifier reasoning."}
                    </div>
                  </div>
                  <DecisionBadge decision={session?.verifier.decision ?? "not_run"} large />
                </div>
              </motion.div>

              <div className="grid gap-3 sm:grid-cols-2">
                <IndicatorCard
                  label="Original failure resolved"
                  value={session ? (session.verifier.originalFailureResolved ? "yes" : "no") : "unknown"}
                  positive={session?.verifier.originalFailureResolved ?? false}
                />
                <IndicatorCard
                  label="Behavior match"
                  value={session?.verifier.behaviorMatchStatus ?? "unknown"}
                  positive={(session?.verifier.behaviorMatchStatus ?? "").includes("matched")}
                />
                <IndicatorCard
                  label="Retry count"
                  value={String(session?.session.attemptsUsed ?? 0)}
                  positive={(session?.session.attemptsUsed ?? 0) <= 1}
                />
                <IndicatorCard
                  label="Session status"
                  value={session?.session.status ?? "idle"}
                  positive={session?.session.finalDecision === "accept"}
                />
              </div>

              <InfoStack title="Uncertainty notes">
                {session?.verifier.uncertaintyNotes ?? "No verifier uncertainty notes yet."}
              </InfoStack>

              <TokenList
                title="Regression flags"
                values={session?.verifier.regressionFlags ?? []}
                emptyLabel="No regression flags recorded."
              />
              <TokenList
                title="Retry feedback"
                values={session?.verifier.targetedFeedbackForRetry ?? []}
                emptyLabel="No retry feedback for this session."
              />
            </div>
          </Panel>
        </motion.section>

        <motion.section id="explorer" {...sectionMotion}>
          <Panel
            eyebrow="Session Explorer"
            title="Trace, diff, retries, and artifacts in one place"
            subtitle="The detail surfaces are grouped into tabs so the main screen stays readable while deep technical evidence remains easy to inspect."
          >
            <div className="grid gap-5">
              <SegmentedControl
                value={explorerTab}
                options={[
                  { value: "trace", label: "Trace timeline" },
                  { value: "diff", label: "Patch diff" },
                  { value: "attempts", label: "Patch attempts" },
                  { value: "artifacts", label: "Artifacts" },
                ]}
                onChange={(value) => setExplorerTab(value as ExplorerTab)}
              />

              <AnimatePresence mode="wait">
                {explorerTab === "trace" ? (
                  <motion.div
                    key="trace"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.24 }}
                    className="grid gap-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="font-display text-xl font-semibold text-slate-950">Trace timeline</div>
                        <div className="mt-1 text-sm text-slate-500">
                          Filter events by component and inspect payloads as technical artifacts.
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {traceFilters.map((filter) => (
                          <button
                            key={filter}
                            type="button"
                            onClick={() => setTraceFilter(filter)}
                            className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
                              traceFilter === filter
                                ? "bg-slate-950 text-white"
                                : "border border-slate-300 bg-white text-slate-600 hover:border-slate-400"
                            }`}
                          >
                            {filter}
                          </button>
                        ))}
                      </div>
                    </div>

                    {filteredTraceEvents.length ? (
                      <div className="grid gap-3">
                        {filteredTraceEvents.map((event, index) => (
                          <TraceCard
                            key={`${event.timestamp ?? "trace"}-${index}`}
                            event={event}
                            index={index}
                            onCopy={(value) => void copyText(`trace-${index}`, value)}
                            copied={copiedKey === `trace-${index}`}
                          />
                        ))}
                      </div>
                    ) : (
                      <EmptyState
                        title="No matching trace events"
                        text="Run a case or switch the active filter to reveal saved handoff events."
                      />
                    )}
                  </motion.div>
                ) : null}

                {explorerTab === "diff" ? (
                  <motion.div
                    key="diff"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.24 }}
                    className="grid gap-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="font-display text-xl font-semibold text-slate-950">Patch diff</div>
                        <div className="mt-1 text-sm text-slate-500">
                          Compare original code, patched code, and the unified diff without losing patch metadata.
                        </div>
                      </div>
                      <SegmentedControl
                        value={diffView}
                        options={[
                          { value: "split", label: "Split view" },
                          { value: "unified", label: "Unified diff" },
                        ]}
                        onChange={(value) => setDiffView(value as DiffView)}
                        compact
                      />
                    </div>

                    {session?.latestPatch ? (
                      <div className="grid gap-4">
                        <div className="flex flex-wrap gap-2">
                          <MetaBadge label={`Strategy ${session.latestPatch.strategyId ?? "n/a"}`} tone="info" />
                          <MetaBadge label={`Breadth ${session.latestPatch.minimalityFlag ?? "n/a"}`} tone="neutral" />
                          <MetaBadge
                            label={`Confidence ${formatConfidence(session.latestPatch.confidenceScore)}`}
                            tone="success"
                          />
                        </div>

                        {diffView === "split" ? (
                          <div className="grid gap-4 xl:grid-cols-2">
                            <CodePanel
                              title="Original code"
                              code={session.originalCode}
                              action={
                                <button
                                  type="button"
                                  onClick={() => void copyText("original-code", session.originalCode)}
                                  className="copy-button"
                                >
                                  {copiedKey === "original-code" ? "Copied" : "Copy"}
                                </button>
                              }
                            />
                            <CodePanel
                              title="Patched code"
                              code={session.latestPatch.updatedCode || session.finalPatchedCode || ""}
                              action={
                                <button
                                  type="button"
                                  onClick={() =>
                                    void copyText(
                                      "patched-code",
                                      session.latestPatch?.updatedCode || session.finalPatchedCode || "",
                                    )
                                  }
                                  className="copy-button"
                                >
                                  {copiedKey === "patched-code" ? "Copied" : "Copy"}
                                </button>
                              }
                            />
                          </div>
                        ) : (
                          <DiffPanel
                            title="Unified diff"
                            diffText={session.latestPatch.patchDiff ?? ""}
                            onCopy={() => void copyText("latest-diff", session.latestPatch?.patchDiff ?? "")}
                            copied={copiedKey === "latest-diff"}
                          />
                        )}

                        <InfoStack title="Patch summary">
                          {session.latestPatch.patchSummary ?? "No patch summary available."}
                        </InfoStack>
                      </div>
                    ) : (
                      <EmptyState
                        title="No patch artifact yet"
                        text="This session either stopped conservatively, escalated before a patch was accepted, or started from an already-working script."
                      />
                    )}
                  </motion.div>
                ) : null}

                {explorerTab === "attempts" ? (
                  <motion.div
                    key="attempts"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.24 }}
                    className="grid gap-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="font-display text-xl font-semibold text-slate-950">Intermediate patch attempts</div>
                        <div className="mt-1 text-sm text-slate-500">
                          Switch between retries to see how patch strategy and diff details evolved across attempts.
                        </div>
                      </div>
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                        {session?.patchAttempts.length ?? 0} attempt(s)
                      </span>
                    </div>

                    {session?.patchAttempts.length ? (
                      <div className="grid gap-4">
                        <AttemptStepper
                          attempts={session.patchAttempts}
                          selectedAttemptIndex={selectedAttempt?.attemptIndex ?? 0}
                          onSelect={(attempt) => setSelectedAttemptIndex(Math.max(attempt.attemptIndex - 1, 0))}
                        />

                        {selectedAttempt ? (
                          <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
                            <div className="grid gap-4">
                              <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                                <div className="flex flex-wrap items-center justify-between gap-3">
                                  <div>
                                    <div className="font-display text-lg font-semibold text-slate-950">
                                      Attempt {selectedAttempt.attemptIndex}
                                    </div>
                                    <div className="mt-1 text-sm leading-6 text-slate-600">
                                      {selectedAttempt.patchSummary ?? "No patch summary available."}
                                    </div>
                                  </div>
                                  <div className="flex flex-wrap gap-2">
                                    {selectedAttempt.strategyId ? (
                                      <MetaBadge label={selectedAttempt.strategyId} tone="info" />
                                    ) : null}
                                    {selectedAttempt.minimalityFlag ? (
                                      <MetaBadge label={selectedAttempt.minimalityFlag} tone="neutral" />
                                    ) : null}
                                    <MetaBadge
                                      label={`Confidence ${formatConfidence(selectedAttempt.confidenceScore)}`}
                                      tone="success"
                                    />
                                  </div>
                                </div>
                              </div>
                              <CodePanel title="Patch candidate" code={selectedAttempt.patchCode ?? ""} />
                            </div>
                            <DiffPanel
                              title="Attempt diff"
                              diffText={selectedAttempt.diffText ?? ""}
                              onCopy={() => void copyText(`attempt-diff-${selectedAttempt.attemptIndex}`, selectedAttempt.diffText ?? "")}
                              copied={copiedKey === `attempt-diff-${selectedAttempt.attemptIndex}`}
                            />
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <EmptyState
                        title="No retry history"
                        text="This session either succeeded without retries or never generated an intermediate patch candidate."
                      />
                    )}
                  </motion.div>
                ) : null}

                {explorerTab === "artifacts" ? (
                  <motion.div
                    key="artifacts"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.24 }}
                    className="grid gap-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="font-display text-xl font-semibold text-slate-950">Saved artifacts</div>
                        <div className="mt-1 text-sm text-slate-500">
                          Useful for screenshots, report citations, and local inspection after a run finishes.
                        </div>
                      </div>
                      <SegmentedControl
                        value={artifactPreview}
                        options={[
                          { value: "summary", label: "Summary" },
                          { value: "failure", label: "Failure note" },
                          { value: "paths", label: "File paths" },
                        ]}
                        onChange={(value) => setArtifactPreview(value as ArtifactPreview)}
                        compact
                      />
                    </div>

                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                      <ArtifactCard label="Session folder" value={session?.artifacts.sessionDir} onCopy={copyText} copiedKey={copiedKey} />
                      <ArtifactCard label="Trace JSONL" value={session?.artifacts.tracePath} onCopy={copyText} copiedKey={copiedKey} />
                      <ArtifactCard label="Summary" value={session?.artifacts.summaryPath} onCopy={copyText} copiedKey={copiedKey} />
                      <ArtifactCard label="State snapshot" value={session?.artifacts.stateSnapshotPath} onCopy={copyText} copiedKey={copiedKey} />
                      <ArtifactCard label="Final patch" value={session?.artifacts.finalPatchPath} onCopy={copyText} copiedKey={copiedKey} />
                      <ArtifactCard label="Failure summary" value={session?.artifacts.failureSummaryPath} onCopy={copyText} copiedKey={copiedKey} />
                    </div>

                    <div className="rounded-[26px] border border-slate-200 bg-slate-50 p-4">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                        {artifactPreview === "summary"
                          ? "Summary preview"
                          : artifactPreview === "failure"
                            ? "Failure summary preview"
                            : "Artifact paths"}
                      </div>
                      <pre className="code-scroll mt-3 max-h-[340px] overflow-auto whitespace-pre-wrap rounded-2xl bg-slate-950 p-4 font-mono text-xs leading-6 text-slate-100">
                        {artifactPreview === "summary"
                          ? session?.summaryMarkdown || "No summary markdown available."
                          : artifactPreview === "failure"
                            ? session?.failureSummaryMarkdown || "No failure summary for this session."
                            : JSON.stringify(session?.artifacts ?? {}, null, 2)}
                      </pre>
                    </div>
                  </motion.div>
                ) : null}
              </AnimatePresence>
            </div>
          </Panel>
        </motion.section>

        <motion.section id="evaluation" {...sectionMotion} className="panel-grid lg:grid-cols-[1.05fr_0.95fr]">
          <Panel
            eyebrow="Evaluation Dashboard"
            title="Planned and latest recorded evaluation evidence"
            subtitle="Designed for report-ready screenshots: aggregate metrics first, case outcomes second, and distribution hints without turning into a heavy analytics product."
          >
            <div className="grid gap-4">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                <MetricTile label="Total cases" value={String(evaluationSummary.totalCases)} hint="Core suite size" />
                <MetricTile label="Accepted" value={String(evaluationSummary.accepted)} hint="Successful bounded repairs" positive />
                <MetricTile label="Stopped" value={String(evaluationSummary.failedOrStopped)} hint="Conservative stop outcomes" warning />
                <MetricTile label="Escalated" value={String(evaluationSummary.escalated)} hint="Human review required" />
                <MetricTile label="Avg retries" value={String(evaluationSummary.averageRetries)} hint="Lower is easier to explain" />
                <MetricTile label="Avg latency (ms)" value={String(evaluationSummary.averageLatencyMs)} hint="Saved from latest run" />
              </div>

              <div className="rounded-[26px] border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-display text-lg font-semibold text-slate-950">Outcome distribution</div>
                    <div className="mt-1 text-sm text-slate-500">
                      A lightweight visual summary of accept vs stop vs escalate.
                    </div>
                  </div>
                  <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                    {evaluation?.latestRunPath ? "Latest run" : "Planned cases"}
                  </span>
                </div>

                <div className="mt-4 space-y-3">
                  {evaluationDistribution.map((item) => (
                    <div key={item.label} className="space-y-2">
                      <div className="flex items-center justify-between text-sm text-slate-600">
                        <span>{item.label}</span>
                        <span>{item.value}</span>
                      </div>
                      <div className="h-2.5 overflow-hidden rounded-full bg-slate-200">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: item.width }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                          className={`h-full rounded-full ${chartColors[item.key]}`}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="overflow-hidden rounded-[26px] border border-slate-200">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                    <thead className="bg-slate-50 text-slate-500">
                      <tr>
                        <TableHead>Case</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Outcome</TableHead>
                        <TableHead>Retries</TableHead>
                        <TableHead>Latency</TableHead>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {evaluationRows.map((row) => (
                        <tr
                          key={row.case_id}
                          className={isFailureLike(row) ? "bg-rose-50/40" : ""}
                        >
                          <TableCell>{row.case_id}</TableCell>
                          <TableCell>{row.case_type}</TableCell>
                          <TableCell>
                            <DecisionBadge decision={row.outcome_label ?? row.ideal_system_action} />
                          </TableCell>
                          <TableCell>{row.retry_count ?? "planned"}</TableCell>
                          <TableCell>{row.latency_ms ?? "n/a"}</TableCell>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="text-sm text-slate-500">
                {evaluation?.latestRunPath
                  ? `Latest evaluation run: ${evaluation.latestRunPath}`
                  : "No saved evaluation run found yet. Planned evaluation metadata is displayed instead."}
              </div>
            </div>
          </Panel>

          <Panel
            eyebrow="Failure Analysis"
            title="Two high-value limitation stories"
            subtitle="These cards make it easy to explain why TraceFix is conservative and why bounded automation needs a verifier instead of trusting “no crash” as success."
          >
            <div className="grid gap-4">
              {failureHighlights.map((item, index) => (
                <motion.article
                  key={item.caseId}
                  initial={{ opacity: 0, y: 14 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.2 }}
                  transition={{ delay: index * 0.08, duration: 0.34 }}
                  className="rounded-[28px] border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-5 shadow-sm"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="font-display text-xl font-semibold text-slate-950">{item.title}</div>
                      <div className="mt-1 text-sm text-slate-500">
                        {item.caseInfo?.caseId ?? item.caseId} • current outcome {item.outcome}
                      </div>
                    </div>
                    <DecisionBadge decision={item.outcome} />
                  </div>

                  <div className="mt-5 grid gap-3 text-sm leading-7 text-slate-700">
                    <p><span className="font-semibold text-slate-950">What happened:</span> {item.why}</p>
                    <p><span className="font-semibold text-slate-950">Why verifier rejected:</span> {item.boundary}</p>
                    <p><span className="font-semibold text-slate-950">What this boundary reveals:</span> TraceFix values evidence-backed stopping over over-claiming success.</p>
                    <p><span className="font-semibold text-slate-950">Future improvement:</span> {item.futureFix}</p>
                  </div>
                </motion.article>
              ))}
            </div>
          </Panel>
        </motion.section>

        <motion.section id="final-output" {...sectionMotion}>
          <Panel
            eyebrow="Final Output & Evidence Package"
            title="Submission-ready artifacts from the actual project"
            subtitle="Use this final section to close the video with concrete outputs: evaluation files, traces, session state, patches, report materials, and the honest manual items that still require a human."
          >
            <div className="grid gap-5">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {finalEvidenceItems.map((item) => (
                  <CopyValueCard key={item.label} label={item.label} value={item.value} onCopy={copyText} copiedKey={copiedKey} />
                ))}
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                <InfoStack title="Final contribution">
                  TraceFix demonstrates a bounded, auditable multi-component debugging workflow: execute the script,
                  diagnose the failure, generate a minimal patch, rerun the program, verify behavior, and save evidence.
                </InfoStack>
                <InfoStack title="Honest limitations">
                  The scope is intentionally narrow: single-file Python scripts, beginner-to-intermediate bug classes,
                  bounded retries, local artifacts, and a lightweight course sandbox rather than a hardened security boundary.
                </InfoStack>
                <InfoStack title="Manual submission items">
                  The live video link and final screenshots still require team capture. The frontend shows the material,
                  but it does not fabricate media, AI logs, or submission links.
                </InfoStack>
              </div>
            </div>
          </Panel>
        </motion.section>
      </div>
    </div>
  );
}

function TopBar(props: {
  session: SessionPayload | null;
  decisionTone: ReturnType<typeof getDecisionTone>;
}) {
  return (
    <div className="sticky top-0 z-30">
      <div className="rounded-[22px] border border-white/60 bg-white/80 px-4 py-3 shadow-sm backdrop-blur-xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-sm font-semibold text-white shadow-lg shadow-slate-950/10">
              TF
            </div>
            <div>
              <div className="font-display text-lg font-semibold text-slate-950">TraceFix</div>
              <div className="text-sm text-slate-500">Modern local visualization for a bounded debugging workflow</div>
            </div>
          </div>

          <nav className="hidden flex-wrap items-center gap-2 lg:flex">
            {[
              ["#demo-roadmap", "Video Roadmap"],
              ["#workspace", "Workspace"],
              ["#session-story", "Pipeline"],
              ["#explorer", "Explorer"],
              ["#evaluation", "Evaluation"],
              ["#final-output", "Final Output"],
            ].map(([href, label]) => (
              <a
                key={href}
                href={href}
                className="rounded-full px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
              >
                {label}
              </a>
            ))}
          </nav>

          <div className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-semibold ${props.decisionTone.pillClass}`}>
            <span className={`h-2.5 w-2.5 rounded-full ${props.decisionTone.dotClass}`} />
            {props.session?.session.finalDecision ?? "ready"}
          </div>
        </div>
      </div>
    </div>
  );
}

function DemoStepCard(props: {
  step: { time: string; title: string; action: string };
  index: number;
}) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.25 }}
      transition={{ delay: props.index * 0.04, duration: 0.28 }}
      className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
    >
      <div className="flex flex-wrap items-start gap-3">
        <span className="rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-white">
          {props.step.time}
        </span>
        <div className="min-w-0 flex-1">
          <div className="font-display text-lg font-semibold text-slate-950">{props.step.title}</div>
          <div className="mt-2 text-sm leading-7 text-slate-600">{props.step.action}</div>
        </div>
      </div>
    </motion.article>
  );
}

function CoverageCard(props: { requirement: string; location: string; status: string }) {
  return (
    <div className="rounded-[22px] border border-emerald-200 bg-emerald-50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-display text-base font-semibold text-slate-950">{props.requirement}</div>
          <div className="mt-2 text-sm leading-6 text-emerald-800">{props.location}</div>
        </div>
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-800">
          {props.status}
        </span>
      </div>
    </div>
  );
}

function CopyValueCard(props: {
  label: string;
  value: string;
  onCopy: (key: string, value: string | null | undefined) => Promise<void>;
  copiedKey: string;
}) {
  const copyKey = `final-${props.label}`;
  return (
    <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.label}</div>
        <button type="button" onClick={() => void props.onCopy(copyKey, props.value)} className="copy-button">
          {props.copiedKey === copyKey ? "Copied" : "Copy"}
        </button>
      </div>
      <div className="mt-3 break-all font-mono text-xs leading-6 text-slate-700">{props.value}</div>
    </div>
  );
}

function StickySessionBar(props: {
  loading: boolean;
  session: SessionPayload | null;
  decisionTone: ReturnType<typeof getDecisionTone>;
}) {
  return (
    <motion.div
      layout
      className="sticky top-[78px] z-20 rounded-[24px] border border-slate-200 bg-white/88 px-4 py-3 shadow-sm backdrop-blur-xl"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Current session</span>
          <div className="font-mono text-sm text-slate-700">
            {props.session?.session.sessionId ?? "No session yet"}
          </div>
          <div className="hidden h-5 w-px bg-slate-200 sm:block" />
          <div className="text-sm text-slate-500">
            {props.loading
              ? "Running controller flow..."
              : props.session
                ? `${props.session.session.targetFile} • ${props.session.session.attemptsUsed}/${props.session.session.maxAttempts} attempt(s)`
                : "Load a case and run TraceFix to create a session."}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${props.decisionTone.pillClass}`}>
            {props.loading ? "running" : props.session?.session.finalDecision ?? "idle"}
          </span>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-600">
            handoffs {props.session?.session.handoffCount ?? 0}
          </span>
        </div>
      </div>
    </motion.div>
  );
}

function Panel(props: { eyebrow: string; title: string; subtitle: string; children: ReactNode }) {
  return (
    <section className="rounded-[30px] border border-slate-200 bg-white/92 p-6 shadow-panel backdrop-blur-sm">
      <div className="mb-5 space-y-2">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.eyebrow}</div>
        <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950">{props.title}</h2>
        <p className="max-w-3xl text-sm leading-7 text-slate-600">{props.subtitle}</p>
      </div>
      {props.children}
    </section>
  );
}

function MiniSignalCard(props: { label: string; value: string; helper: string }) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/5 p-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.label}</div>
      <div className="mt-2 text-lg font-semibold text-white">{props.value}</div>
      <div className="mt-1 text-sm text-slate-400">{props.helper}</div>
    </div>
  );
}

function SegmentedControl(props: {
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
  compact?: boolean;
}) {
  return (
    <div className={`inline-flex flex-wrap items-center gap-2 rounded-full border border-slate-200 bg-slate-50 p-1 ${props.compact ? "self-start" : ""}`}>
      {props.options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => props.onChange(option.value)}
          className={`rounded-full px-3 py-2 text-sm font-medium transition ${
            props.value === option.value
              ? "bg-white text-slate-950 shadow-sm"
              : "text-slate-500 hover:text-slate-900"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function CaseBadge(props: { group: CaseItem["group"]; badge: string }) {
  const classes =
    props.group === "happy_path"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : props.group === "governance"
        ? "border-violet-200 bg-violet-50 text-violet-700"
        : "border-rose-200 bg-rose-50 text-rose-700";
  return <span className={`rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${classes}`}>{props.badge}</span>;
}

function CaseInfo(props: { label: string; value: string }) {
  return (
    <div className="rounded-[20px] border border-white/70 bg-white p-3 shadow-sm">
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.label}</div>
      <div className="mt-2 text-sm leading-6 text-slate-700">{props.value}</div>
    </div>
  );
}

function PipelineVisualizer(props: {
  pipeline: PipelineStep[];
  loading: boolean;
  liveStepIndex: number;
  attemptsUsed: number;
  finalDecision: string;
}) {
  return (
    <div className="grid gap-4">
      <div className="grid gap-3 lg:grid-cols-5">
        {props.pipeline.map((step, index) => (
          <motion.div
            key={step.id}
            layout
            className={`relative overflow-hidden rounded-[24px] border p-4 transition ${
              isActiveStep(step.status)
                ? "border-cyan-300 bg-cyan-50 shadow-sm ring-2 ring-cyan-100"
                : "border-slate-200 bg-slate-50"
            }`}
            animate={{
              y: props.loading && index === props.liveStepIndex ? -2 : 0,
              scale: props.loading && index === props.liveStepIndex ? 1.01 : 1,
            }}
            transition={{ duration: 0.22 }}
          >
            {index < props.pipeline.length - 1 ? (
              <div className="pointer-events-none absolute right-[-24px] top-1/2 hidden h-px w-10 -translate-y-1/2 bg-gradient-to-r from-cyan-400/70 to-violet-400/70 lg:block" />
            ) : null}
            <div className="flex items-start justify-between gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-slate-950 text-sm font-semibold text-white">
                {index + 1}
              </div>
              <StatusPill status={step.status} />
            </div>
            <div className="mt-4 font-display text-lg font-semibold text-slate-950">{step.label}</div>
            <div className="mt-2 text-sm leading-6 text-slate-600">{step.detail}</div>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <StoryCard label="Retries" value={`${props.attemptsUsed}`} />
        <StoryCard label="Current flow" value={props.loading ? "Active handoff animation" : "Trace-backed state"} />
        <StoryCard label="Decision path" value={props.finalDecision} />
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: StepStatus }) {
  const styles: Record<StepStatus, string> = {
    idle: "bg-slate-200 text-slate-700",
    running: "bg-cyan-100 text-cyan-800",
    success: "bg-emerald-100 text-emerald-800",
    retry: "bg-amber-100 text-amber-800",
    failure: "bg-rose-100 text-rose-800",
    escalated: "bg-violet-100 text-violet-800",
    stopped: "bg-slate-300 text-slate-700",
  };
  return <span className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${styles[status]}`}>{status}</span>;
}

function StoryCard(props: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.label}</div>
      <div className="mt-3 text-sm leading-7 text-slate-700">{props.value}</div>
    </div>
  );
}

function IndicatorCard(props: { label: string; value: string; positive: boolean }) {
  return (
    <div className={`rounded-[22px] border p-4 ${props.positive ? "border-emerald-200 bg-emerald-50" : "border-slate-200 bg-slate-50"}`}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.label}</div>
      <div className="mt-3 flex items-center gap-3">
        <span className={`h-3 w-3 rounded-full ${props.positive ? "bg-emerald-500" : "bg-slate-400"}`} />
        <div className="text-lg font-semibold text-slate-950">{props.value}</div>
      </div>
    </div>
  );
}

function DecisionBadge(props: { decision: string; large?: boolean }) {
  const tone = getDecisionTone(props.decision);
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] ${props.large ? tone.pillClassLarge : tone.pillClass}`}>
      <span className={`h-2.5 w-2.5 rounded-full ${tone.dotClass}`} />
      {props.decision}
    </span>
  );
}

function InfoStack(props: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.title}</div>
      <div className="mt-3 text-sm leading-7 text-slate-700">{props.children}</div>
    </div>
  );
}

function TokenList(props: { title: string; values: string[]; emptyLabel: string }) {
  return (
    <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.title}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {props.values.length ? (
          props.values.map((value) => (
            <span key={value} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
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

function TraceCard(props: {
  event: TraceEvent;
  index: number;
  onCopy: (value: string) => void;
  copied: boolean;
}) {
  const component = getTraceComponent(props.event);
  const eventLabel = props.event.handoff ?? props.event.event ?? "trace_event";
  return (
    <details className="group rounded-[24px] border border-slate-200 bg-slate-50 open:bg-white">
      <summary className="list-none cursor-pointer px-4 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-600">
                #{props.index + 1}
              </span>
              <span className="rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-700">
                {component}
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                {props.event.event ?? "handoff"}
              </span>
            </div>
            <div className="font-display text-lg font-semibold text-slate-950">{eventLabel}</div>
            <div className="text-sm leading-6 text-slate-600">{props.event.summary ?? "No summary"}</div>
          </div>

          <div className="flex flex-col items-end gap-2">
            <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600">
              attempt {props.event.attempt_index ?? 0}
            </span>
            <span className="text-xs uppercase tracking-[0.18em] text-slate-400">
              {props.event.timestamp ?? "no timestamp"}
            </span>
          </div>
        </div>
      </summary>

      <div className="border-t border-slate-200 px-4 py-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Payload</div>
          <button
            type="button"
            onClick={() => props.onCopy(JSON.stringify(props.event.payload ?? {}, null, 2))}
            className="copy-button"
          >
            {props.copied ? "Copied" : "Copy payload"}
          </button>
        </div>
        <pre className="code-scroll overflow-x-auto rounded-2xl bg-slate-950 p-4 text-xs leading-6 text-slate-100">
          {JSON.stringify(props.event.payload ?? {}, null, 2)}
        </pre>
      </div>
    </details>
  );
}

function MetaBadge(props: { label: string; tone: "info" | "neutral" | "success" }) {
  const classes =
    props.tone === "info"
      ? "border-cyan-200 bg-cyan-50 text-cyan-700"
      : props.tone === "success"
        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
        : "border-slate-200 bg-slate-50 text-slate-700";
  return <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${classes}`}>{props.label}</span>;
}

function CodePanel(props: { title: string; code: string; action?: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-slate-200 bg-slate-950">
      <div className="flex items-center justify-between gap-3 border-b border-slate-800 px-4 py-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.title}</div>
        {props.action}
      </div>
      <pre className="code-scroll max-h-[420px] overflow-auto whitespace-pre-wrap p-4 font-mono text-xs leading-6 text-slate-100">
        {props.code || "No code available."}
      </pre>
    </div>
  );
}

function DiffPanel(props: {
  title: string;
  diffText: string;
  onCopy?: () => void;
  copied?: boolean;
}) {
  if (!props.diffText) {
    return <EmptyState title="No diff yet" text="This patch attempt does not have a unified diff artifact." />;
  }

  return (
    <div className="overflow-hidden rounded-[24px] border border-slate-200 bg-slate-950">
      <div className="flex items-center justify-between gap-3 border-b border-slate-800 px-4 py-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.title}</div>
        {props.onCopy ? (
          <button type="button" onClick={props.onCopy} className="copy-button">
            {props.copied ? "Copied" : "Copy diff"}
          </button>
        ) : null}
      </div>
      <pre className="code-scroll max-h-[420px] overflow-auto whitespace-pre-wrap p-4 font-mono text-xs leading-6">
        {props.diffText.split("\n").map((line, index) => (
          <div
            key={`${line}-${index}`}
            className={
              line.startsWith("+")
                ? "text-emerald-300"
                : line.startsWith("-")
                  ? "text-rose-300"
                  : line.startsWith("@@")
                    ? "text-cyan-300"
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

function AttemptStepper(props: {
  attempts: PatchAttempt[];
  selectedAttemptIndex: number;
  onSelect: (attempt: PatchAttempt) => void;
}) {
  return (
    <div className="flex flex-wrap gap-3">
      {props.attempts.map((attempt) => {
        const active = props.selectedAttemptIndex === attempt.attemptIndex;
        return (
          <button
            key={attempt.attemptIndex}
            type="button"
            onClick={() => props.onSelect(attempt)}
            className={`rounded-[22px] border px-4 py-3 text-left transition ${
              active
                ? "border-cyan-300 bg-cyan-50 ring-2 ring-cyan-100"
                : "border-slate-200 bg-slate-50 hover:border-slate-300"
            }`}
          >
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Attempt</div>
            <div className="mt-1 text-lg font-semibold text-slate-950">{attempt.attemptIndex}</div>
            <div className="mt-2 text-xs text-slate-500">{attempt.strategyId ?? "No strategy recorded"}</div>
          </button>
        );
      })}
    </div>
  );
}

function ArtifactCard(props: {
  label: string;
  value?: string | null;
  onCopy: (key: string, value: string | null | undefined) => Promise<void>;
  copiedKey: string;
}) {
  const copyKey = `artifact-${props.label}`;
  return (
    <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.label}</div>
        <button type="button" onClick={() => void props.onCopy(copyKey, props.value)} className="copy-button">
          {props.copiedKey === copyKey ? "Copied" : "Copy"}
        </button>
      </div>
      <div className="mt-3 break-all font-mono text-xs leading-6 text-slate-700">{props.value ?? "Not available"}</div>
    </div>
  );
}

function MetricTile(props: { label: string; value: string; hint: string; positive?: boolean; warning?: boolean }) {
  const tone = props.warning
    ? "border-amber-200 bg-amber-50"
    : props.positive
      ? "border-emerald-200 bg-emerald-50"
      : "border-slate-200 bg-slate-50";
  return (
    <div className={`rounded-[24px] border p-4 ${tone}`}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{props.label}</div>
      <div className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{props.value}</div>
      <div className="mt-2 text-sm text-slate-600">{props.hint}</div>
    </div>
  );
}

function EmptyState(props: { title: string; text: string }) {
  return (
    <div className="rounded-[24px] border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-center">
      <div className="font-display text-lg font-semibold text-slate-900">{props.title}</div>
      <div className="mt-2 text-sm leading-7 text-slate-500">{props.text}</div>
    </div>
  );
}

function TableHead(props: { children: ReactNode }) {
  return <th className="px-4 py-3 font-semibold">{props.children}</th>;
}

function TableCell(props: { children: ReactNode }) {
  return <td className="px-4 py-3 align-top text-slate-700">{props.children}</td>;
}

function getDecisionTone(decision: string) {
  const normalized = decision.toLowerCase();
  if (normalized === "accept" || normalized === "fixed" || normalized === "success") {
    return {
      panelClass: "border-emerald-200 bg-emerald-50 text-emerald-900",
      pillClass: "bg-emerald-100 text-emerald-800",
      pillClassLarge: "bg-emerald-100 text-emerald-800",
      dotClass: "bg-emerald-500",
    };
  }
  if (normalized === "retry") {
    return {
      panelClass: "border-amber-200 bg-amber-50 text-amber-900",
      pillClass: "bg-amber-100 text-amber-800",
      pillClassLarge: "bg-amber-100 text-amber-800",
      dotClass: "bg-amber-500",
    };
  }
  if (normalized === "escalate" || normalized === "escalated_for_human_review") {
    return {
      panelClass: "border-violet-200 bg-violet-50 text-violet-900",
      pillClass: "bg-violet-100 text-violet-800",
      pillClassLarge: "bg-violet-100 text-violet-800",
      dotClass: "bg-violet-500",
    };
  }
  if (normalized === "stop" || normalized === "stopped_no_patch" || normalized === "max_attempts_reached") {
    return {
      panelClass: "border-rose-200 bg-rose-50 text-rose-900",
      pillClass: "bg-rose-100 text-rose-800",
      pillClassLarge: "bg-rose-100 text-rose-800",
      dotClass: "bg-rose-500",
    };
  }
  return {
    panelClass: "border-slate-200 bg-slate-50 text-slate-900",
    pillClass: "bg-slate-100 text-slate-700",
    pillClassLarge: "bg-slate-100 text-slate-700",
    dotClass: "bg-slate-400",
  };
}

function stringifyRecordValue(record: Record<string, unknown> | undefined | null, key: string): string | null {
  if (!record) {
    return null;
  }
  const value = record[key];
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return null;
}

function getTraceComponent(event: TraceEvent): string {
  if (event.handoff) {
    return event.handoff.split("->")[0]?.trim() ?? "system";
  }
  return event.event ?? "system";
}

function isFailureLike(row: EvaluationRow): boolean {
  const outcome = (row.outcome_label ?? row.ideal_system_action ?? "").toLowerCase();
  return outcome === "stop" || outcome === "escalate" || outcome === "max_attempts_reached";
}

function formatConfidence(value: number | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(2);
}

function isActiveStep(status: StepStatus): boolean {
  return status === "running" || status === "retry" || status === "escalated";
}

export default App;
