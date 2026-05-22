import React from "react";
import { CheckSquare, MessageCircle } from "lucide-react";
import { CardBlock } from "../ui/CardBlock";
import { WidgetCard } from "../ui/WidgetCard";
import { SignalRow } from "../ui/SignalRow";
import { personalWidgets, asterSignals } from "../../data/mockData";

export function RightPanel({ light }: any) {
  return (
    <div className="space-y-4">
      <CardBlock title="Active Projects & Goals" light={light} icon={CheckSquare}>
        {personalWidgets.map((widget) => <WidgetCard key={widget.title} widget={widget} light={light} />)}
      </CardBlock>
      <CardBlock title="Aster Signals" light={light} icon={MessageCircle}>
        {asterSignals.map((note) => <SignalRow key={note.title} note={note} light={light} />)}
      </CardBlock>
    </div>
  );
}
