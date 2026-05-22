import React, { useEffect, useState } from "react";
import { Activity, AlertTriangle, RefreshCw } from "lucide-react";
import { cls } from "../utils/formatting";
import { fetchStatus, type StatusResponse } from "../lib/api";

interface StatusViewProps {
  light: boolean;
}

export function StatusView({ light }: StatusViewProps) {
  const [data, setData] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const next = await fetchStatus();
        if (!cancelled) {
          setData(next);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to connect to SORA API");
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

  const cardClass = cls(
    "rounded-[2rem] border p-5",
    light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]",
  );

  return (
    <div className="space-y-4">
      <section className={cardClass}>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-cyan-500/15 text-cyan-300">
              <Activity className="h-6 w-6" />
            </div>
            <div>
              <div className="text-sm text-slate-400">SORA Runtime</div>
              <h2 className="mt-1 text-2xl font-semibold tracking-tight">System Status</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                `/api/status` の read-only レポートを表示します。
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setRefreshTick((value) => value + 1)}
            disabled={loading}
            className={cls(
              "inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium transition",
              light
                ? "border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 disabled:text-slate-400"
                : "border border-white/10 bg-black/20 text-slate-100 hover:bg-white/10 disabled:text-slate-500",
            )}
          >
            <RefreshCw className={cls("h-4 w-4", loading && "animate-spin")} />
            Refresh
          </button>
        </div>
      </section>

      <section className={cardClass}>
        {loading ? (
          <div className="py-8 text-sm text-slate-400">Loading SORA status...</div>
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
              <div className="font-medium">Failed to connect to SORA API</div>
              <div className="mt-1 opacity-80">{error}</div>
            </div>
          </div>
        ) : null}

        {!loading && !error && data ? (
          <div
            className={cls(
              "rounded-[1.5rem] border px-4 py-4 text-sm leading-7 whitespace-pre-wrap",
              light ? "border-slate-200 bg-slate-50 text-slate-700" : "border-white/10 bg-black/20 text-slate-200",
            )}
          >
            {data.report}
          </div>
        ) : null}
      </section>
    </div>
  );
}
