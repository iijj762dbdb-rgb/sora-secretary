import React, { useEffect, useState } from "react";
import { CheckSquare, RefreshCw } from "lucide-react";
import { cls } from "../../utils/formatting";
import { fetchTodos, type TodoItem } from "../../lib/api";
import { CardBlock } from "./CardBlock";

interface TodoPanelProps {
  light: boolean;
  compact?: boolean;
}

function formatDate(value?: string | null): string {
  if (!value) return "no date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ja-JP", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function toneForPriority(priority?: string | null): string {
  if (priority === "high") return "bg-rose-500/15 text-rose-300";
  if (priority === "low") return "bg-slate-500/15 text-slate-300";
  return "bg-cyan-500/15 text-cyan-300";
}

export function TodoPanel({ light, compact = false }: TodoPanelProps) {
  const [items, setItems] = useState<TodoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const payload = await fetchTodos("all");
        if (!cancelled) {
          setItems(payload.items.filter((item) => item.status === "todo" || item.status === "doing"));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load ToDos");
          setItems([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [refreshTick]);

  return (
    <CardBlock
      title="Active ToDos"
      light={light}
      icon={CheckSquare}
      headerRight={
        <button
          type="button"
          onClick={() => setRefreshTick((value) => value + 1)}
          disabled={loading}
          className={cls(
            "inline-flex items-center gap-2 rounded-2xl px-3 py-2 text-xs font-medium transition",
            light
              ? "border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 disabled:text-slate-400"
              : "border border-white/10 bg-black/20 text-slate-100 hover:bg-white/10 disabled:text-slate-500",
          )}
        >
          <RefreshCw className={cls("h-3.5 w-3.5", loading && "animate-spin")} />
          Refresh
        </button>
      }
    >
      {loading ? <div className="py-6 text-sm text-slate-400">Loading ToDos...</div> : null}
      {!loading && error ? <div className="py-6 text-sm text-amber-400">Failed to load ToDos: {error}</div> : null}
      {!loading && !error && !items.length ? <div className="py-6 text-sm text-slate-400">Active ToDo はありません。</div> : null}
      {!loading && !error && items.length
        ? items.slice(0, compact ? 3 : 6).map((item) => (
            <div
              key={item.id}
              className={cls(
                "rounded-2xl border p-3",
                light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium">{item.text}</div>
                  <div className="mt-1 flex flex-wrap gap-2 text-[11px] text-slate-500">
                    <span className="uppercase tracking-[0.15em]">{item.status}</span>
                    <span className={cls("rounded-full px-2 py-0.5", toneForPriority(item.priority))}>
                      {item.priority || "normal"}
                    </span>
                    {item.due_at ? <span>due {formatDate(item.due_at)}</span> : null}
                  </div>
                </div>
                <div className="shrink-0 text-right text-[10px] text-slate-500">
                  <div>{item.id}</div>
                  <div>{formatDate(item.updated_at)}</div>
                </div>
              </div>
            </div>
          ))
        : null}
    </CardBlock>
  );
}
