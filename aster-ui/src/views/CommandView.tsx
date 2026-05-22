import React from "react";
import { Command, Send, Sparkles } from "lucide-react";
import { cls } from "../utils/formatting";
import { ChatBubble } from "../components/aster/ChatBubble";
import { commandActions } from "../data/mockData";

export function CommandView({ light, input, setInput, messages, setMessages, runAsterAction }: any) {
  const submitText = () => {
    const text = input.trim();
    if (!text) return;
    setMessages((items: any) => [...items, { role: "user", text }, { role: "assistant", text: "了解しました。これはモックなので、実際のLLM接続前の返信として表示しています。" }]);
    setInput("");
  };

  return (
    <section className={cls("flex min-h-[calc(100vh-150px)] flex-col rounded-[2rem] border", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
      <div className="border-b border-white/10 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm text-slate-400"><Command className="h-4 w-4" /> ASTER ACTIONS</div>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {commandActions.map((action) => {
            const Icon = action.icon;
            return (
              <button key={action.label} onClick={() => runAsterAction(action)} className={cls("flex items-center gap-3 rounded-2xl border p-3 text-left text-sm transition", light ? "border-slate-200 bg-slate-50 hover:bg-white" : "border-white/10 bg-black/20 hover:bg-white/10")}>
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-cyan-500/15 text-cyan-300"><Icon className="h-4 w-4" /></span>
                <span>
                  <span className="block font-medium">{action.label}</span>
                  <span className="text-[11px] text-slate-400">実行してAsterに確認</span>
                </span>
              </button>
            );
          })}
        </div>
      </div>
      <div className="flex-1 space-y-6 overflow-auto p-4">
        {messages.map((message: any, index: number) => <ChatBubble key={`\${message.role}-\${index}`} message={message} light={light} />)}
      </div>
      <div className="p-4">
        <div className={cls("flex items-center gap-2 rounded-[1.6rem] border p-2", light ? "border-slate-200 bg-slate-50" : "border-white/10 bg-black/20")}>
          <Sparkles className="ml-2 h-5 w-5 text-cyan-300" />
          <input value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => event.key === "Enter" && submitText()} placeholder="Ask Aster..." className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm outline-none placeholder:text-slate-500" />
          <button onClick={submitText} className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-r from-indigo-500 to-cyan-500 text-white"><Send className="h-5 w-5" /></button>
        </div>
      </div>
    </section>
  );
}
