import React from "react";
import { cls } from "../../utils/formatting";
import type { MemoryItem } from "../../lib/api";

interface MemoryCardProps {
  memory: MemoryItem;
  light: boolean;
  isTimeline?: boolean;
  selected?: boolean;
  onClick?: () => void;
}

function formatTags(tags: MemoryItem["tags"]): string[] {
  if (Array.isArray(tags)) {
    return tags.filter(Boolean).map((tag) => String(tag).trim()).filter(Boolean);
  }

  if (typeof tags === "string") {
    return tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
  }

  return [];
}

function formatDate(value?: string | null): string {
  if (!value) return "time unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ja-JP", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function MemoryCard({
  memory,
  light,
  isTimeline = false,
  selected = false,
  onClick,
}: MemoryCardProps) {
  const tags = formatTags(memory.tags);
  const preview = memory.summary || memory.body || "本文はありません。";

  return (
    <button
      type="button"
      onClick={onClick}
      className={cls(
        "w-full rounded-[1.6rem] border p-4 text-left transition",
        light ? "bg-slate-50" : "bg-black/20",
        selected
          ? "border-cyan-400/70 shadow-lg shadow-cyan-500/10"
          : light
            ? "border-slate-200 hover:border-cyan-400/50"
            : "border-white/10 hover:border-cyan-400/50",
      )}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-wrap gap-2">
          <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.18em] text-cyan-300">
            {memory.memory_type || "memory"}
          </span>
          {tags.slice(0, 2).map((tag) => (
            <span
              key={`${memory.id}-${tag}`}
              className={cls(
                "rounded-full px-2 py-0.5 text-[10px]",
                light ? "bg-slate-200 text-slate-700" : "bg-white/10 text-slate-300",
              )}
            >
              {tag}
            </span>
          ))}
        </div>
        <span className="shrink-0 text-[11px] text-slate-500">{formatDate(memory.created_at)}</span>
      </div>
      <h4 className="font-medium">{memory.title}</h4>
      <p className={cls("mt-2 text-sm leading-relaxed", light ? "text-slate-600" : "text-slate-400")}>
        {preview}
      </p>
      {isTimeline ? null : tags.length > 2 ? (
        <div className="mt-3 text-[11px] text-slate-500">+{tags.length - 2} tags</div>
      ) : null}
    </button>
  );
}
