import React from "react";
import { motion } from "framer-motion";
import { Orbit } from "lucide-react";
import { cls } from "../../utils/formatting";

export function AsterOrb({ small = false }: { small?: boolean }) {
  return (
    <motion.div animate={{ rotate: 360 }} transition={{ duration: 18, repeat: Infinity, ease: "linear" }} className={cls("relative grid shrink-0 place-items-center rounded-full bg-gradient-to-br from-indigo-400 via-violet-500 to-cyan-300 shadow-2xl shadow-cyan-500/20", small ? "h-14 w-14" : "h-32 w-32")}>
      <div className="absolute inset-2 rounded-full border border-white/40" />
      <div className="absolute inset-5 rounded-full bg-[#080b13]/85 backdrop-blur" />
      <Orbit className={cls("relative text-cyan-100", small ? "h-6 w-6" : "h-12 w-12")} />
      <span className="absolute right-2 top-2 h-3 w-3 rounded-full bg-cyan-200 shadow-lg shadow-cyan-300" />
    </motion.div>
  );
}
