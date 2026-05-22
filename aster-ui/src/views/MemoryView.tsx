import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { RefreshCw, Search, AlertTriangle, Brain } from "lucide-react";
import { cls } from "../utils/formatting";
import { MemoryCard } from "../components/ui/MemoryCard";
import {
  fetchMemoryDetail,
  fetchRecentMemories,
  searchMemories,
  type MemoryItem,
} from "../lib/api";

interface MemoryViewProps {
  light: boolean;
}

function formatTags(tags: MemoryItem["tags"]): string[] {
  if (Array.isArray(tags)) {
    return tags.filter(Boolean).map((tag) => String(tag).trim()).filter(Boolean);
  }

  if (typeof tags === "string") {
    return tags.split(",").map((tag) => tag.trim()).filter(Boolean);
  }

  return [];
}

function formatDate(value?: string | null): string {
  if (!value) return "unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function MemoryView({ light }: MemoryViewProps) {
  const [viewMode, setViewMode] = useState<"grid" | "timeline">("grid");
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [items, setItems] = useState<MemoryItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedMemory, setSelectedMemory] = useState<MemoryItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadList() {
      setLoading(true);
      setError(null);

      try {
        const payload = submittedQuery.trim()
          ? await searchMemories(submittedQuery.trim(), 20)
          : await fetchRecentMemories(20);

        if (cancelled) return;

        setItems(payload.items);

        if (!payload.items.length) {
          setSelectedId(null);
          setSelectedMemory(null);
          setDetailError(null);
          return;
        }

        const nextSelectedId = payload.items.some((item) => item.id === selectedId)
          ? selectedId
          : payload.items[0]?.id ?? null;

        setSelectedId(nextSelectedId);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load memories");
          setItems([]);
          setSelectedId(null);
          setSelectedMemory(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadList();
    return () => {
      cancelled = true;
    };
  }, [submittedQuery, refreshTick]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedMemory(null);
      setDetailError(null);
      return;
    }

    const memoryId = selectedId;
    let cancelled = false;

    async function loadDetail() {
      setDetailLoading(true);
      setDetailError(null);

      try {
        const detail = await fetchMemoryDetail(memoryId);
        if (!cancelled) {
          setSelectedMemory(detail);
        }
      } catch (err) {
        if (!cancelled) {
          setDetailError(err instanceof Error ? err.message : "Failed to load memory detail");
          setSelectedMemory(null);
        }
      } finally {
        if (!cancelled) {
          setDetailLoading(false);
        }
      }
    }

    void loadDetail();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const boxClass = cls(
    "rounded-[2rem] border",
    light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]",
  );

  const runSearch = () => {
    setSubmittedQuery(query.trim());
  };

  const resetToRecent = () => {
    setQuery("");
    setSubmittedQuery("");
    setRefreshTick((value) => value + 1);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className={cls("flex flex-1 items-center gap-3 rounded-[2rem] border p-3", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
          <Search className="h-5 w-5 text-cyan-300" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                runSearch();
              }
            }}
            placeholder="SORAの記憶を検索…"
            className="min-w-0 flex-1 bg-transparent py-2 text-sm outline-none"
          />
          <button
            type="button"
            onClick={runSearch}
            className="rounded-[1.4rem] bg-gradient-to-r from-indigo-500 to-cyan-500 px-4 py-2 text-sm font-medium text-white"
          >
            Search
          </button>
        </div>
        <button
          type="button"
          onClick={() => setRefreshTick((value) => value + 1)}
          disabled={loading}
          className={cls(
            "inline-flex items-center justify-center gap-2 rounded-[2rem] border px-4 py-3 text-sm font-medium transition",
            light
              ? "border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:text-slate-400"
              : "border-white/10 bg-white/[0.045] text-slate-100 hover:bg-white/10 disabled:text-slate-500",
          )}
        >
          <RefreshCw className={cls("h-4 w-4", loading && "animate-spin")} />
          Refresh
        </button>
        <div className={cls("flex shrink-0 gap-1 rounded-[2rem] border p-1", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
          <button onClick={() => setViewMode("grid")} className={cls("rounded-[1.5rem] px-4 py-2 text-sm font-medium", viewMode === "grid" ? "bg-gradient-to-r from-indigo-500 to-cyan-500 text-white" : "text-slate-400")}>Grid</button>
          <button onClick={() => setViewMode("timeline")} className={cls("rounded-[1.5rem] px-4 py-2 text-sm font-medium", viewMode === "timeline" ? "bg-gradient-to-r from-indigo-500 to-cyan-500 text-white" : "text-slate-400")}>Timeline</button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <section className={cls(boxClass, "p-4")}>
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <div className="text-sm text-slate-400">
                {submittedQuery ? `Search results for "${submittedQuery}"` : "Recent memories"}
              </div>
              <div className="mt-1 text-xs text-slate-500">{items.length} items</div>
            </div>
            {submittedQuery ? (
              <button
                type="button"
                onClick={resetToRecent}
                className={cls(
                  "rounded-2xl px-3 py-2 text-xs font-medium transition",
                  light ? "bg-slate-100 text-slate-700 hover:bg-slate-200" : "bg-white/10 text-slate-200 hover:bg-white/15",
                )}
              >
                Back to recent
              </button>
            ) : null}
          </div>

          {loading ? (
            <div className="py-8 text-sm text-slate-400">Loading memories...</div>
          ) : null}

          {!loading && error ? (
            <div
              className={cls(
                "flex items-start gap-3 rounded-[1.5rem] border px-4 py-4 text-sm",
                light ? "border-amber-200 bg-amber-50 text-amber-900" : "border-amber-500/20 bg-amber-500/10 text-amber-100",
              )}
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <div className="font-medium">Failed to load memories</div>
                <div className="mt-1 opacity-80">{error}</div>
              </div>
            </div>
          ) : null}

          {!loading && !error && !items.length ? (
            <div className="rounded-[1.5rem] border border-dashed border-white/10 px-4 py-10 text-center text-sm text-slate-400">
              {submittedQuery ? "検索条件に一致する記憶はありません。" : "表示できる記憶がまだありません。"}
            </div>
          ) : null}

          {!loading && !error && items.length ? (
            viewMode === "grid" ? (
              <div className="grid gap-4 md:grid-cols-2">
                {items.map((memory) => (
                  <MemoryCard
                    key={memory.id}
                    memory={memory}
                    light={light}
                    selected={memory.id === selectedId}
                    onClick={() => setSelectedId(memory.id)}
                  />
                ))}
              </div>
            ) : (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="relative ml-4 space-y-8 border-l-2 border-white/10 py-4">
                {items.map((memory) => (
                  <motion.div key={memory.id} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ duration: 0.5, ease: "easeOut" }} className="relative pl-8">
                    <span className="absolute left-[-9px] top-4 h-4 w-4 rounded-full border-4 border-[#060712] bg-cyan-400 shadow-lg shadow-cyan-400/30" />
                    <MemoryCard
                      memory={memory}
                      light={light}
                      isTimeline
                      selected={memory.id === selectedId}
                      onClick={() => setSelectedId(memory.id)}
                    />
                  </motion.div>
                ))}
              </motion.div>
            )
          ) : null}
        </section>

        <aside className={cls(boxClass, "p-5")}>
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-500/15 text-cyan-300">
              <Brain className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm text-slate-400">Memory Detail</div>
              <div className="mt-1 text-lg font-semibold">Read-only inspector</div>
            </div>
          </div>

          {detailLoading ? (
            <div className="py-8 text-sm text-slate-400">Loading memory detail...</div>
          ) : null}

          {!detailLoading && detailError ? (
            <div
              className={cls(
                "flex items-start gap-3 rounded-[1.5rem] border px-4 py-4 text-sm",
                light ? "border-amber-200 bg-amber-50 text-amber-900" : "border-amber-500/20 bg-amber-500/10 text-amber-100",
              )}
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <div className="font-medium">Failed to load detail</div>
                <div className="mt-1 opacity-80">{detailError}</div>
              </div>
            </div>
          ) : null}

          {!detailLoading && !detailError && selectedMemory ? (
            <div className="space-y-4">
              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-cyan-300">
                  {selectedMemory.memory_type || "memory"}
                </div>
                <h3 className="mt-2 text-xl font-semibold">{selectedMemory.title}</h3>
                <div className="mt-2 text-xs text-slate-500">{selectedMemory.id}</div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <DetailField label="Created At" value={formatDate(selectedMemory.created_at)} light={light} />
                <DetailField label="Updated At" value={formatDate(selectedMemory.updated_at)} light={light} />
              </div>

              <div>
                <div className="mb-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">Tags</div>
                <div className="flex flex-wrap gap-2">
                  {formatTags(selectedMemory.tags).length ? (
                    formatTags(selectedMemory.tags).map((tag) => (
                      <span
                        key={`${selectedMemory.id}-${tag}`}
                        className={cls(
                          "rounded-full px-3 py-1 text-xs",
                          light ? "bg-slate-100 text-slate-700" : "bg-white/10 text-slate-200",
                        )}
                      >
                        {tag}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-slate-500">No tags</span>
                  )}
                </div>
              </div>

              <div>
                <div className="mb-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">Summary</div>
                <div className={cls("rounded-[1.5rem] border px-4 py-3 text-sm leading-7", light ? "border-slate-200 bg-slate-50 text-slate-700" : "border-white/10 bg-black/20 text-slate-200")}>
                  {selectedMemory.summary || "summary is empty"}
                </div>
              </div>

              <div>
                <div className="mb-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">Body</div>
                <div className={cls("rounded-[1.5rem] border px-4 py-3 text-sm leading-7 whitespace-pre-wrap", light ? "border-slate-200 bg-slate-50 text-slate-700" : "border-white/10 bg-black/20 text-slate-200")}>
                  {selectedMemory.body || "body is empty"}
                </div>
              </div>
            </div>
          ) : null}

          {!detailLoading && !detailError && !selectedMemory && !loading && !error ? (
            <div className="rounded-[1.5rem] border border-dashed border-white/10 px-4 py-10 text-center text-sm text-slate-400">
              表示する記憶を選んでください。
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}

function DetailField({ label, value, light }: { label: string; value: string; light: boolean }) {
  return (
    <div className={cls("rounded-[1.4rem] border px-4 py-3", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
      <div className="text-[11px] uppercase tracking-[0.18em] text-slate-400">{label}</div>
      <div className="mt-2 text-sm">{value}</div>
    </div>
  );
}
