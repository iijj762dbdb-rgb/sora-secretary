export interface StatusResponse {
  status: string;
  report: string;
}

const API_BASE = "http://127.0.0.1:8787";

export async function fetchStatus(): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE}/api/status`);

  if (!response.ok) {
    throw new Error(`status fetch failed (${response.status})`);
  }

  const payload = (await response.json()) as StatusResponse;
  if (payload.status !== "ok") {
    throw new Error("SORA API returned a non-ok status");
  }

  return payload;
}
