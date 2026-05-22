import React from "react";
import { cls } from "../../utils/formatting";

export function MemoryCard({ memory, light, isTimeline = false }: any) {
  return (
    <div className={cls("rounded-[1.6rem] border p-4 transition hover:border-cyan-400/50", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
      <div className="mb-2 flex items-center justify-between">
        <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-[10px] font-medium text-cyan-300">{memory.tag}</span>
        <span className="text-[11px] text-slate-500">{memory.time}</span>
      </div>
      <h4 className="font-medium">{memory.title}</h4>
      <p className="mt-2 text-sm text-slate-400 leading-relaxed">{memory.body}</p>
    </div>
  );
}
