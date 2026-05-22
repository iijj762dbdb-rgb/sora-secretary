import React from "react";
import { cls } from "../../utils/formatting";
import { Sparkles } from "lucide-react";

export function SignalRow({ note, light }: any) {
  return (
    <div className={cls("flex items-start gap-3 rounded-2xl border p-3", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
      <div className={cls("mt-0.5 h-2 w-2 rounded-full", note.level === "active" ? "bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" : note.level === "stable" ? "bg-emerald-400" : "bg-indigo-400")} />
      <div>
        <div className="text-sm font-medium">{note.title}</div>
        <div className="mt-1 text-xs text-slate-400 leading-relaxed">{note.body}</div>
      </div>
    </div>
  );
}
