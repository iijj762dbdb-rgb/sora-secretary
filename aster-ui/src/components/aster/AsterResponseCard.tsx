import React from "react";
import { Sparkles } from "lucide-react";
import { cls, parseAsterMarkdown, getAsterNextActions } from "../../utils/formatting";

export function AsterResponseCard({ message, light }: any) {
  const blocks = parseAsterMarkdown(message.text);
  const nextActions = getAsterNextActions(message.text);
  return (
    <div className="flex justify-start">
      <div className={cls("max-w-[92%] overflow-hidden rounded-[1.7rem] border shadow-2xl", light ? "border-slate-200 bg-white" : "border-white/10 bg-slate-950/80 shadow-cyan-500/5")}>
        <div className={cls("flex items-center justify-between border-b px-5 py-3", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-white/[0.04]")}>
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-2xl bg-cyan-500/15 text-cyan-300"><Sparkles className="h-4 w-4" /></div>
            <div>
              <div className="text-sm font-semibold">Aster Response</div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">structured result</div>
            </div>
          </div>
          <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-[11px] font-medium text-emerald-300">done</span>
        </div>
        <div className="p-5 text-sm leading-6">
          <AsterMarkdownBlocks blocks={blocks} light={light} />
          {nextActions.length > 0 && (
            <div className={cls("mt-5 rounded-2xl border p-3", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
              <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Next actions</div>
              <div className="flex flex-wrap gap-2">
                {nextActions.map((action) => <button key={action} className="rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs text-cyan-100 transition hover:bg-cyan-400/20">{action}</button>)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AsterMarkdownBlocks({ blocks, light }: any) {
  return (
    <div className="space-y-3">
      {blocks.map((block: any, index: number) => {
        if (block.type === "heading") return <h3 key={index} className="mt-4 text-base font-semibold text-cyan-300 first:mt-0">{block.text}</h3>;
        if (block.type === "list") return <ul key={index} className="list-inside list-disc space-y-1 text-slate-300">{block.items.map((item: string) => <li key={item}>{item}</li>)}</ul>;
        if (block.type === "table") return <AsterTable key={index} rows={block.rows} light={light} />;
        return <p key={index} className="leading-relaxed">{block.text}</p>;
      })}
    </div>
  );
}

function AsterTable({ rows, light }: any) {
  if (rows.length === 0) return null;
  const [header, ...body] = rows;
  return (
    <div className="overflow-hidden rounded-2xl border border-white/10">
      <table className="w-full text-left text-xs">
        <thead className={light ? "bg-slate-200/70" : "bg-white/10"}>
          <tr>{header.map((cell: string) => <th key={cell} className="px-3 py-2 font-semibold text-cyan-300">{cell}</th>)}</tr>
        </thead>
        <tbody>
          {body.map((row: string[], rowIndex: number) => (
            <tr key={rowIndex} className="border-t border-white/10">
              {row.map((cell: string, cellIndex: number) => <td key={`\${rowIndex}-\${cellIndex}`} className="px-3 py-2 text-slate-300">{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
