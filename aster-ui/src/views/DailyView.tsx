import React from "react";
import { CalendarDays, Archive } from "lucide-react";
import { cls } from "../utils/formatting";
import { CardBlock } from "../components/ui/CardBlock";
import { MemoryRow } from "../components/ui/MemoryRow";
import { dailyReports } from "../data/mockData";

export function DailyView({ light }: any) {
  return (
    <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <section className={cls("rounded-[2rem] border p-5", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
        <div className="mb-4 flex items-center gap-3"><CalendarDays className="h-5 w-5 text-cyan-300" /><h2 className="text-lg font-semibold">Daily Generator</h2></div>
        <textarea className={cls("min-h-56 w-full rounded-[1.6rem] border p-4 text-sm outline-none", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")} placeholder="今日やったこと、決めたこと、次にやることを雑に入力…" />
        <button className="mt-4 rounded-2xl bg-gradient-to-r from-indigo-500 to-cyan-500 px-5 py-3 text-sm font-medium text-white shadow-lg shadow-cyan-500/20">Asterに整形して保存</button>
      </section>
      <CardBlock title="Daily Archive" light={light} icon={Archive}>{dailyReports.map((report) => <MemoryRow key={report.date} memory={{ title: report.title, body: report.body, time: report.date }} light={light} />)}</CardBlock>
    </div>
  );
}
