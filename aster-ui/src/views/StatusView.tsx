import React from "react";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { cls } from "../utils/formatting";
import { statusItems } from "../data/mockData";

export function StatusView({ light }: any) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {statusItems.map((item) => {
        const Icon = item.icon;
        return (
          <div key={item.label} className={cls("rounded-[2rem] border p-5", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
            <div className="mb-4 flex items-center justify-between"><div className="grid h-12 w-12 place-items-center rounded-2xl bg-cyan-500/15 text-cyan-300"><Icon className="h-6 w-6" /></div>{item.tone === "good" ? <CheckCircle2 className="h-5 w-5 text-cyan-400" /> : <AlertTriangle className="h-5 w-5 text-amber-400" />}</div>
            <div className="text-sm text-slate-400">{item.label}</div>
            <div className="mt-1 text-2xl font-semibold">{item.value}</div>
            <div className="mt-2 text-xs text-slate-500">{item.detail}</div>
          </div>
        );
      })}
    </div>
  );
}
