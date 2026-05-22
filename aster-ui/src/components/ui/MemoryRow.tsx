import React from "react";
import { cls } from "../../utils/formatting";

export function MemoryRow({ memory, light }: any) {
  return (
    <div className={cls("flex items-start justify-between gap-3 rounded-2xl border p-3", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
      <div>
        <div className="text-sm font-medium">{memory.title}</div>
        <div className="mt-1 text-xs text-slate-400">{memory.body}</div>
      </div>
      <div className="shrink-0 text-right text-[11px] text-slate-500">
        <div>{memory.tag}</div>
        <div>{memory.time}</div>
      </div>
    </div>
  );
}
