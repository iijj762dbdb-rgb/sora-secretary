import React from "react";
import { cls } from "../../utils/formatting";

export function ActionButton({ icon: Icon, label, sub, onClick }: any) {
  return (
    <button onClick={onClick} className="flex items-center gap-3 rounded-[1.4rem] bg-white/5 p-3 transition hover:bg-white/10 w-full text-left">
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-cyan-500/15 text-cyan-300">
        <Icon className="h-5 w-5" />
      </span>
      <span>
        <span className="block font-medium">{label}</span>
        <span className="text-[11px] text-slate-400">{sub}</span>
      </span>
    </button>
  );
}
