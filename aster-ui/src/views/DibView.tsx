import React, { useState } from "react";
import { Brain, Layers, MessageCircle } from "lucide-react";
import { cls } from "../utils/formatting";
import { CardBlock } from "../components/ui/CardBlock";
import { SignalRow } from "../components/ui/SignalRow";
import { DibInspector } from "../components/dib/DibInspector";
import { asterSignals, dibItems, commandActions } from "../data/mockData";

export function DibView({ light, runAsterAction }: any) {
  const [selected, setSelected] = useState(null);
  return (
    <>
      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <section className={cls("relative overflow-hidden rounded-[2rem] border p-5", light ? "border-slate-200 bg-white" : "border-white/10 bg-[#0a0f1d]")}>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-cyan-100"><Layers className="h-3.5 w-3.5" /> DIB LINKED</div>
          <h2 className="text-3xl font-semibold tracking-tight">Aster + Document Inbox</h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">OCR・写真・書類・アーカイブ・検索の入口です。</p>
          <div className="mt-5 flex flex-wrap gap-3"><button onClick={() => runAsterAction(commandActions[2])} className="rounded-2xl bg-gradient-to-r from-indigo-500 to-cyan-500 px-5 py-3 text-sm font-medium text-white shadow-lg shadow-cyan-500/20">InboxをAsterに整理させる</button></div>
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <InboxQueue light={light} setSelected={setSelected} />
            <WorkflowPanel light={light} />
          </div>
        </section>
        <div className="space-y-4">
          <CardBlock title="DIB Signals" light={light} icon={MessageCircle}>{asterSignals.map((note) => <SignalRow key={note.title} note={note} light={light} />)}</CardBlock>
        </div>
      </div>
      <DibInspector item={selected} onClose={() => setSelected(null)} light={light} />
    </>
  );
}

function InboxQueue({ light, setSelected }: any) {
  return (
    <div className={cls("rounded-[1.6rem] border p-4", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
      <div className="mb-3 flex items-center gap-2 text-sm font-medium"><Layers className="h-4 w-4 text-cyan-300" /> Inbox Queue</div>
      <div className="space-y-3">
        {dibItems.map((item) => (
          <button key={item.id} onClick={() => setSelected(item)} className={cls("flex w-full items-center justify-between gap-3 rounded-2xl border p-3 text-left transition hover:border-cyan-400/50", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/5")}>
            <div className="min-w-0 flex-1"><div className="truncate text-sm font-medium">{item.name}</div><div className="mt-1 text-xs text-slate-400">{item.state}</div></div>
            <div className="text-xs text-slate-500">{item.time}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

function WorkflowPanel({ light }: any) {
  return (
    <div className={cls("rounded-[1.6rem] border p-4", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
      <div className="mb-4 flex items-center gap-2 text-sm font-medium"><Brain className="h-4 w-4 text-cyan-300" /> Aster Workflow</div>
      <div className="space-y-4">
        <WorkflowStep title="Inbox" body="写真・PDF・メモを受け取る" />
        <WorkflowStep title="OCR" body="文字起こしと内容抽出" />
        <WorkflowStep title="Memory" body="関連する記憶へ接続" />
        <WorkflowStep title="Archive" body="sora archiveへ安全に保存" />
      </div>
    </div>
  );
}

function WorkflowStep({ title, body }: any) {
  return (
    <div className="flex flex-col">
      <span className="text-sm font-medium text-slate-200">{title}</span>
      <span className="text-xs text-slate-400">{body}</span>
    </div>
  );
}
