import React, { useState } from "react";
import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { cls } from "../utils/formatting";
import { MemoryCard } from "../components/ui/MemoryCard";
import { memories } from "../data/mockData";

export function MemoryView({ light }: any) {
  const [viewMode, setViewMode] = useState("grid");
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className={cls("flex flex-1 items-center gap-3 rounded-[2rem] border p-3", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
          <Search className="h-5 w-5 text-cyan-300" />
          <input placeholder="SORAの記憶を検索…" className="min-w-0 flex-1 bg-transparent py-2 text-sm outline-none" />
        </div>
        <div className={cls("flex shrink-0 gap-1 rounded-[2rem] border p-1", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
          <button onClick={() => setViewMode("grid")} className={cls("rounded-[1.5rem] px-4 py-2 text-sm font-medium", viewMode === "grid" ? "bg-gradient-to-r from-indigo-500 to-cyan-500 text-white" : "text-slate-400")}>Grid</button>
          <button onClick={() => setViewMode("timeline")} className={cls("rounded-[1.5rem] px-4 py-2 text-sm font-medium", viewMode === "timeline" ? "bg-gradient-to-r from-indigo-500 to-cyan-500 text-white" : "text-slate-400")}>Timeline</button>
        </div>
      </div>
      {viewMode === "grid" ? (
        <div className="grid gap-4 md:grid-cols-2">{memories.map((memory) => <MemoryCard key={memory.title} memory={memory} light={light} />)}</div>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="relative ml-4 space-y-8 border-l-2 border-white/10 py-4">
          {memories.map((memory) => (
            <motion.div key={memory.title} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ duration: 0.5, ease: "easeOut" }} className="relative pl-8">
              <span className="absolute left-[-9px] top-4 h-4 w-4 rounded-full border-4 border-[#060712] bg-cyan-400 shadow-lg shadow-cyan-400/30" />
              <MemoryCard memory={memory} light={light} isTimeline />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
