import React, { useEffect, useMemo, useState } from "react";
import { cls } from "./utils/formatting";
import { navItems, initialMessages } from "./data/mockData";
import { DesktopSidebar } from "./components/layout/DesktopSidebar";
import { MobileNav } from "./components/layout/MobileNav";
import { TopBar } from "./components/layout/TopBar";
import { RightPanel } from "./components/layout/RightPanel";
import { HomeView } from "./views/HomeView";
import { CommandView } from "./views/CommandView";
import { MemoryView } from "./views/MemoryView";
import { DailyView } from "./views/DailyView";
import { StatusView } from "./views/StatusView";
import { DibView } from "./views/DibView";

const validNavIds = new Set(navItems.map((item) => item.id));

function getInitialActiveView() {
  if (typeof window === "undefined") return "home";

  const hashView = window.location.hash.replace(/^#\/?/, "");
  if (validNavIds.has(hashView)) return hashView;

  const pathView = window.location.pathname.split("/").filter(Boolean).at(-1) ?? "";
  if (validNavIds.has(pathView)) return pathView;

  return "home";
}

export default function App() {
  const [active, setActive] = useState(getInitialActiveView);
  const [light, setLight] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState(initialMessages);
  
  const current = useMemo(() => navItems.find((item) => item.id === active) ?? navItems[0], [active]);
  const CurrentIcon = current.icon;

  useEffect(() => {
    const nextHash = `#/${active}`;
    if (window.location.hash !== nextHash) {
      window.history.replaceState(null, "", nextHash);
    }
  }, [active]);

  useEffect(() => {
    const syncFromLocation = () => {
      const next = getInitialActiveView();
      setActive((currentView) => (currentView === next ? currentView : next));
    };

    window.addEventListener("hashchange", syncFromLocation);
    window.addEventListener("popstate", syncFromLocation);
    return () => {
      window.removeEventListener("hashchange", syncFromLocation);
      window.removeEventListener("popstate", syncFromLocation);
    };
  }, []);

  const runAsterAction = (action: any) => {
    setMessages((items) => [
      ...items,
      { role: "user", text: `［実行］\${action.label}` },
      { role: "assistant", text: action.response, markdown: true },
    ]);
    setActive("chat");
  };

  return (
    <div className={cls("min-h-screen overflow-hidden transition-colors", light ? "bg-slate-100 text-slate-950" : "bg-[#060712] text-slate-100")}>
      <BackgroundGlow />
      <div className="relative mx-auto flex min-h-screen max-w-7xl gap-4 p-3 md:p-5">
        <DesktopSidebar active={active} setActive={setActive} light={light} />
        <main className="flex min-w-0 flex-1 flex-col gap-4 pb-24 lg:pb-0">
          <TopBar current={current} CurrentIcon={CurrentIcon} light={light} setLight={setLight} />
          {active === "home" && <HomeView light={light} setActive={setActive} runAsterAction={runAsterAction} />}
          {active === "chat" && <CommandView light={light} input={input} setInput={setInput} messages={messages} setMessages={setMessages} runAsterAction={runAsterAction} />}
          {active === "memory" && <MemoryView light={light} />}
          {active === "daily" && <DailyView light={light} />}
          {active === "status" && <StatusView light={light} />}
          {active === "dib" && <DibView light={light} runAsterAction={runAsterAction} />}
        </main>
        <aside className={cls("hidden w-80 shrink-0 rounded-[2rem] border p-4 xl:block", light ? "border-slate-200 bg-white" : "border-white/10 bg-white/[0.045]")}>
          <RightPanel light={light} />
        </aside>
      </div>
      <MobileNav active={active} setActive={setActive} light={light} />
    </div>
  );
}

function BackgroundGlow() {
  return (
    <div className="pointer-events-none fixed inset-0 opacity-80">
      <div className="absolute left-[-10%] top-[-10%] h-96 w-96 rounded-full bg-indigo-600/20 blur-3xl" />
      <div className="absolute bottom-[-12%] right-[-8%] h-[30rem] w-[30rem] rounded-full bg-cyan-500/15 blur-3xl" />
      <div className="absolute left-1/2 top-1/3 h-72 w-72 -translate-x-1/2 rounded-full bg-fuchsia-500/10 blur-3xl" />
    </div>
  );
}
