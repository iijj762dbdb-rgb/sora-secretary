import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sparkles, X } from "lucide-react";
import { cls } from "../../utils/formatting";
import { DocumentPreview } from "./DocumentPreview";

export function DibInspector({ item, onClose, light }: any) {
  return (
    <AnimatePresence>
      {item && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-[#060712]/80 p-4 backdrop-blur-sm">
          <motion.div initial={{ scale: 0.95, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: 20 }} className={cls("relative w-full max-w-4xl overflow-hidden rounded-[2rem] border shadow-2xl", light ? "border-slate-200 bg-white" : "border-white/20 bg-[#0a0f1d]")}>
            <div className="flex items-center justify-between border-b border-white/10 p-4">
              <div><h3 className="font-semibold">{item.name}</h3><p className="text-xs text-slate-400">DIB Inspector / {item.state}</p></div>
              <button onClick={onClose} className="rounded-full bg-white/10 p-2 hover:bg-white/20"><X className="h-5 w-5" /></button>
            </div>
            <div className="grid h-[60vh] md:grid-cols-2">
              <div className="min-h-0 border-r border-white/10 bg-black/20"><DocumentPreview fileUrl={item.previewUrl} fileType={item.type} fileName={item.name} /></div>
              <div className="flex flex-col bg-white/5 p-6">
                <div className="mb-2 flex items-center justify-between text-sm text-cyan-300"><span className="flex items-center gap-2"><Sparkles className="h-4 w-4" /> AI Extracted Text</span><button className="text-xs hover:text-white">再スキャン</button></div>
                <textarea className={cls("flex-1 resize-none rounded-2xl border p-4 text-sm leading-relaxed outline-none", light ? "border-slate-200 bg-white text-slate-800" : "border-white/10 bg-black/40 text-slate-200")} defaultValue={item.ocrText} />
                <div className="mt-4 flex gap-3"><button onClick={onClose} className="flex-1 rounded-2xl border border-white/10 bg-white/5 py-3 text-sm font-medium hover:bg-white/10">キャンセル</button><button onClick={onClose} className="flex-1 rounded-2xl bg-gradient-to-r from-indigo-500 to-cyan-500 py-3 text-sm font-medium text-white shadow-lg shadow-cyan-500/20">保存して記憶へ</button></div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
