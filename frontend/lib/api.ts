import type {
  GraphData,
  ReportDataResponse,
  ReportResponse,
  SimulationCreateRequest,
  SimulationDetail,
  SimulationSummary,
} from "./types";

// The browser goes through the /api rewrite. Server components cannot fetch
// a relative URL, so they call the backend directly.
const API_BASE =
  typeof window === "undefined"
    ? `${process.env.BACKEND_URL ?? "http://localhost:8000"}/api`
    : "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function createSimulation(
  req: SimulationCreateRequest
): Promise<{ id: string; status: string }> {
  return request("/simulations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function listSimulations(): Promise<SimulationSummary[]> {
  return request("/simulations");
}

export async function getSimulation(id: string): Promise<SimulationDetail> {
  return request(`/simulations/${id}`);
}

export async function deleteSimulation(id: string): Promise<void> {
  return request(`/simulations/${id}`, { method: "DELETE" });
}

export async function getGraph(simId: string): Promise<GraphData> {
  return request(`/simulations/${simId}/graph`);
}

export async function getReport(simId: string): Promise<ReportResponse> {
  return request(`/reports/${simId}`);
}

export async function getReportData(
  simId: string
): Promise<ReportDataResponse> {
  return request(`/reports/${simId}/data`);
}
