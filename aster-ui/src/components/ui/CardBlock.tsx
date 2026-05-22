import React from "react";
import { cls } from "../../utils/formatting";

export function CardBlock({ title, light, icon: Icon, headerRight, children }: any) {
  return (
    <section className={cls("rounded-[2rem] border p-5", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold tracking-wide">{title}</h3>
        <div className="flex items-center gap-3">
          {headerRight}
          {Icon && <Icon className="h-4 w-4 text-slate-400" />}
        </div>
      </div>
      <div className="space-y-3">{children}</div>
    </section>
  );
}
