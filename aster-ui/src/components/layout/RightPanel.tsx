import React from "react";
import { MessageCircle } from "lucide-react";
import { SignalRow } from "../ui/SignalRow";
import { ReminderPanel } from "../ui/ReminderPanel";
import { TodoPanel } from "../ui/TodoPanel";
import { CardBlock } from "../ui/CardBlock";
import { asterSignals } from "../../data/mockData";

export function RightPanel({ light }: any) {
  return (
    <div className="space-y-4">
      <TodoPanel light={light} />
      <ReminderPanel light={light} />
      <CardBlock title="Aster Signals" light={light} icon={MessageCircle}>
        {asterSignals.map((note) => <SignalRow key={note.title} note={note} light={light} />)}
      </CardBlock>
    </div>
  );
}
