import React from "react";
import { motion } from "framer-motion";
import { Brain, Layers, Sparkles } from "lucide-react";
import { cls } from "../utils/formatting";
import { AsterOrb } from "../components/aster/AsterOrb";
import { ActionButton } from "../components/ui/ActionButton";
import { CardBlock } from "../components/ui/CardBlock";
import { MemoryRow } from "../components/ui/MemoryRow";
import { TodoPanel } from "../components/ui/TodoPanel";
import { commandActions, memories } from "../data/mockData";

export function HomeView({ light, setActive, runAsterAction }: any) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
      <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#070b14] p-5 lg:hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.18),transparent_45%)]" />
        <div className="relative flex flex-col items-center text-center">
          <div className="mb-3 mt-2 text-[11px] uppercase tracking-[0.35em] text-cyan-200/70">ASTER ONLINE</div>
          <div className="relative mb-5">
            <div className="absolute inset-0 animate-pulse rounded-full bg-cyan-400/20 blur-2xl" />
            <AsterOrb />
          </div>
          <h2 className="text-3xl font-semibold tracking-tight">Good morning.</h2>
          <p className="mt-2 max-w-xs text-sm leading-6 text-slate-400">Aster は、今日の記録・整理・Inbox処理を待機しています。</p>
          <div className="mt-7 grid w-full gap-3">
            {commandActions.map((action) => <ActionButton key={action.label} icon={action.icon} label={action.label} sub="Asterが実行して反応" onClick={() => runAsterAction(action)} />)}
          </div>
        </div>
      </section>

      <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className={cls("relative hidden overflow-hidden rounded-[2rem] border p-5 lg:block", light ? "border-slate-200 bg-white" : "border-white/10 bg-[#0a0f1d]")}>
        <div className="absolute right-[-8rem] top-[-8rem] h-80 w-80 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="relative grid gap-6 md:grid-cols-[auto_1fr] md:items-center">
          <AsterOrb />
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-cyan-100"><Sparkles className="h-3.5 w-3.5" /> ASTER SIGNAL</div>
            <h2 className="text-3xl font-semibold tracking-tight md:text-5xl">Aster is quietly organizing your world.</h2>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-300">依頼・記憶・日報・状態確認を、“操作と整理”として扱うローカル秘書UIです。</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button onClick={() => setActive("chat")} className="rounded-2xl bg-gradient-to-r from-indigo-500 to-cyan-500 px-5 py-3 text-sm font-medium text-white shadow-lg shadow-cyan-500/20">Ask Aster</button>
              <button onClick={() => setActive("memory")} className="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium">Memory Stream</button>
            </div>
          </div>
        </div>
      </motion.section>

      <section className={cls("relative overflow-hidden rounded-[2rem] border p-4", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-semibold tracking-wide">Command Deck</h3>
          <Layers className="h-4 w-4 text-slate-400" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          {commandActions.map((action) => <ActionButton key={action.label} icon={action.icon} label={action.label} sub="Asterが反応" onClick={() => runAsterAction(action)} />)}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:col-span-2">
        <CardBlock title="Memory Stream" light={light} icon={Brain}>
          {memories.slice(0, 3).map((memory) => <MemoryRow key={memory.title} memory={memory} light={light} />)}
        </CardBlock>
        <div className="xl:hidden">
          <TodoPanel light={light} compact />
        </div>
      </section>
    </div>
  );
}
