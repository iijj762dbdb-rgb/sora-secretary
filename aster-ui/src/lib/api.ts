export interface StatusResponse {
  status: string;
  report: string;
}

export interface MemoryItem {
  id: string;
  title: string;
  summary?: string | null;
  body?: string | null;
  tags?: string[] | string | null;
  memory_type?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MemoriesResponse {
  status: string;
  items: MemoryItem[];
}

interface MemoryDetailResponse {
  status: string;
  item: MemoryItem;
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


export async function fetchRecentMemories(limit = 20): Promise<MemoriesResponse> {
  const response = await fetch(`${API_BASE}/api/memories/recent?limit=${limit}`);

  if (!response.ok) {
    throw new Error(`recent memories fetch failed (${response.status})`);
  }

  const payload = (await response.json()) as MemoriesResponse;
  if (payload.status !== "ok") {
    throw new Error("SORA API returned a non-ok status");
  }

  return payload;
}


export async function searchMemories(query: string, limit = 20): Promise<MemoriesResponse> {
  const response = await fetch(
    `${API_BASE}/api/memories/search?q=${encodeURIComponent(query)}&limit=${limit}`,
  );

  if (!response.ok) {
    throw new Error(`memory search failed (${response.status})`);
  }

  const payload = (await response.json()) as MemoriesResponse;
  if (payload.status !== "ok") {
    throw new Error("SORA API returned a non-ok status");
  }

  return payload;
}


export async function fetchMemoryDetail(memoryId: string): Promise<MemoryItem> {
  const response = await fetch(`${API_BASE}/api/memories/${encodeURIComponent(memoryId)}`);

  if (!response.ok) {
    throw new Error(`memory detail fetch failed (${response.status})`);
  }

  const payload = (await response.json()) as MemoryDetailResponse;
  if (payload.status !== "ok") {
    throw new Error("SORA API returned a non-ok status");
  }

  return payload.item;
}
