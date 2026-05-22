import React from "react";
import { Moon, Sun } from "lucide-react";
import { cls } from "../../utils/formatting";

export function TopBar({ current, CurrentIcon, light, setLight }: any) {
  return (
    <header className={cls("sticky top-3 z-20 flex items-center justify-between rounded-[1.7rem] border px-4 py-3 backdrop-blur-xl", light ? "border-slate-200 bg-white/80" : "border-white/10 bg-[#0c1020]/80")}>
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl bg-indigo-500/15 text-cyan-300 lg:hidden">
          <CurrentIcon className="h-5 w-5" />
        </div>
        <div>
          <div className="text-xs text-slate-400">SORA Secretary / ASTER / {current.label}</div>
          <h1 className="text-xl font-semibold tracking-wide">{current.jp}</h1>
        </div>
      </div>
      <button onClick={() => setLight((value: boolean) => !value)} className={cls("grid h-11 w-11 place-items-center rounded-2xl border", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-white/5")}>
        {light ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
      </button>
    </header>
  );
}
