import React from "react";
import { cls } from "../../utils/formatting";

export function WidgetCard({ widget, light }: any) {
  const Icon = widget.icon;
  return (
    <div className={cls("flex items-center gap-4 rounded-2xl border p-3", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
      <div className={cls("grid h-10 w-10 shrink-0 place-items-center rounded-xl", widget.tone === "warn" ? "bg-amber-500/15 text-amber-400" : "bg-emerald-500/15 text-emerald-400")}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium">{widget.title}</div>
        <div className="mt-0.5 text-[11px] text-slate-400">{widget.subtitle}</div>
        <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/10">
          <div className={cls("h-full rounded-full", widget.tone === "warn" ? "bg-amber-400" : "bg-emerald-400")} style={{ width: `\${widget.progress}%` }} />
        </div>
      </div>
      <div className="text-[10px] text-slate-500">{widget.info}</div>
    </div>
  );
}
