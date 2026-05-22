import React from "react";
import { CircleDot, Sparkles } from "lucide-react";
import { cls } from "../../utils/formatting";
import { AsterOrb } from "../aster/AsterOrb";
import { navItems } from "../../data/mockData";

export function DesktopSidebar({ active, setActive, light }: any) {
  return (
    <aside className={cls("hidden w-72 shrink-0 rounded-[2rem] border p-4 shadow-2xl lg:block", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
      <div className="mb-7 rounded-[1.8rem] border border-white/10 bg-gradient-to-br from-indigo-500/20 via-violet-500/10 to-cyan-400/10 p-4">
        <div className="mb-4 flex items-center gap-3">
          <AsterOrb small />
          <div>
            <div className="text-lg font-semibold tracking-wide">ASTER</div>
            <div className="text-xs text-cyan-200/70">SORA Secretary Intelligence</div>
          </div>
        </div>
        <div className="rounded-2xl bg-black/20 p-3 text-xs leading-5 text-slate-300">Aster は、SORA 内で動作するローカル秘書AIです。記憶・整理・状態管理を束ねます。</div>
      </div>
      <nav className="space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const selected = active === item.id;
          return (
            <button key={item.id} onClick={() => setActive(item.id)} className={cls("group flex w-full items-center gap-3 rounded-3xl px-4 py-3 text-left text-sm transition", selected ? "bg-gradient-to-r from-indigo-500 to-cyan-500 text-white shadow-lg shadow-cyan-500/20" : light ? "text-slate-600 hover:bg-slate-100" : "text-slate-300 hover:bg-white/10")}>
              <Icon className="h-5 w-5" />
              <div className="min-w-0 flex-1">
                <div className="font-medium">{item.label}</div>
                <div className={cls("text-[11px]", selected ? "text-white/75" : "text-slate-500")}>{item.jp}</div>
              </div>
              {selected && <CircleDot className="h-4 w-4" />}
            </button>
          );
        })}
      </nav>
      <div className={cls("mt-7 rounded-[1.8rem] border p-4", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
        <div className="mb-3 flex items-center justify-between text-xs text-slate-400">
          <span>Aster Runtime</span>
          <Sparkles className="h-4 w-4 text-cyan-300" />
        </div>
        <div className="font-medium">gemma3:4b</div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
          <div className="h-full w-2/3 rounded-full bg-gradient-to-r from-indigo-400 to-cyan-300" />
        </div>
      </div>
    </aside>
  );
}
