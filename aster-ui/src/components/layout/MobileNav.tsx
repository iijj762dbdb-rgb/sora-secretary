import React from "react";
import { Orbit } from "lucide-react";
import { cls } from "../../utils/formatting";
import { navItems } from "../../data/mockData";

export function MobileNav({ active, setActive, light }: any) {
  return (
    <>
      <div className="pointer-events-none fixed inset-x-0 top-0 z-10 h-40 bg-gradient-to-b from-cyan-500/10 to-transparent lg:hidden" />
      <button onClick={() => setActive("chat")} className="fixed bottom-24 right-4 z-30 rounded-full border border-cyan-400/20 bg-gradient-to-br from-indigo-500 to-cyan-500 p-4 shadow-2xl shadow-cyan-500/30 lg:hidden">
        <Orbit className="h-7 w-7 text-white" />
      </button>
      <nav className={cls("fixed inset-x-3 bottom-3 z-30 grid grid-cols-6 rounded-[1.7rem] border p-2 shadow-2xl backdrop-blur-xl lg:hidden", light ? "border-slate-200 bg-white/90" : "border-white/10 bg-[#0d1322]/90")}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const selected = active === item.id;
          return (
            <button key={item.id} onClick={() => setActive(item.id)} className={cls("flex flex-col items-center gap-1 rounded-2xl px-1 py-2 text-[10px]", selected ? "bg-gradient-to-r from-indigo-500 to-cyan-500 text-white" : "text-slate-400")}>
              <Icon className="h-5 w-5" />
              {item.jp}
            </button>
          );
        })}
      </nav>
    </>
  );
}
