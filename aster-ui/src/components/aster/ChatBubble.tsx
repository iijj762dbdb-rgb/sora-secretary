import React from "react";
import { cls } from "../../utils/formatting";
import { AsterResponseCard } from "./AsterResponseCard";

export function ChatBubble({ message, light }: any) {
  const isUser = message.role === "user";
  if (isUser || !message.markdown) {
    return (
      <div className={cls("flex", isUser ? "justify-end" : "justify-start")}>
        <div className={cls("max-w-[88%] rounded-[1.5rem] px-5 py-4 text-sm leading-6", isUser ? "bg-gradient-to-r from-indigo-500 to-cyan-500 text-white" : light ? "bg-slate-100 text-slate-800" : "bg-slate-900 text-slate-100")}>
          {message.text}
        </div>
      </div>
    );
  }
  return <AsterResponseCard message={message} light={light} />;
}
