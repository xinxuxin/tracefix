import type { CaseItem, EvaluationSnapshot, SessionPayload } from "./types";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      typeof payload.error === "string" ? payload.error : `Request failed: ${response.status}`,
    );
  }
  return (await response.json()) as T;
}

export async function fetchCases(): Promise<CaseItem[]> {
  const payload = await fetchJson<{ cases: CaseItem[] }>("/api/cases");
  return payload.cases;
}

export async function fetchLatestSession(): Promise<SessionPayload | null> {
  const payload = await fetchJson<{ session: SessionPayload | null }>("/api/latest-session");
  return payload.session;
}

export async function fetchEvaluation(): Promise<EvaluationSnapshot> {
  return fetchJson<EvaluationSnapshot>("/api/evaluation");
}

export async function runDebugSession(input: {
  code: string;
  filename: string;
  expectedOutput: string | null;
  maxRetries: number;
}): Promise<SessionPayload> {
  const payload = await fetchJson<{ session: SessionPayload }>("/api/run", {
    method: "POST",
    body: JSON.stringify(input),
  });
  return payload.session;
}
