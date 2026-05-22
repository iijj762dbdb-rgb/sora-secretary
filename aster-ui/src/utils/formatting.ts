export function cls(...values: (string | undefined | null | false)[]): string {
  return values.filter(Boolean).join(" ");
}

export function buildMockPreviewUrl(title: string, subtitle: string): string {
  const safeTitle = String(title).replace(/[<>&]/g, "");
  const safeSubtitle = String(subtitle).replace(/[<>&]/g, "");
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="1200" viewBox="0 0 900 1200">
      <rect width="900" height="1200" fill="#0a0f1d"/>
      <rect x="80" y="80" width="740" height="1040" rx="34" fill="#f8fafc"/>
      <text x="130" y="170" fill="#0f172a" font-size="38" font-family="sans-serif" font-weight="700">\${safeTitle}</text>
      <text x="130" y="225" fill="#64748b" font-size="26" font-family="sans-serif">\${safeSubtitle}</text>
      <rect x="130" y="300" width="640" height="26" rx="13" fill="#cbd5e1"/>
      <rect x="130" y="360" width="520" height="22" rx="11" fill="#e2e8f0"/>
      <rect x="130" y="420" width="610" height="22" rx="11" fill="#e2e8f0"/>
      <rect x="130" y="520" width="640" height="360" rx="24" fill="#dbeafe"/>
      <circle cx="245" cy="640" r="70" fill="#22d3ee" opacity="0.55"/>
      <rect x="360" y="610" width="280" height="28" rx="14" fill="#0f172a" opacity="0.75"/>
      <rect x="360" y="665" width="220" height="22" rx="11" fill="#334155" opacity="0.55"/>
      <rect x="130" y="940" width="640" height="24" rx="12" fill="#cbd5e1"/>
      <rect x="130" y="995" width="480" height="20" rx="10" fill="#e2e8f0"/>
    </svg>
  `;
  return `data:image/svg+xml;charset=utf-8,\${encodeURIComponent(svg)}`;
}

export function parseAsterMarkdown(text: string) {
  const lines = String(text || "").split("\\n");
  const blocks: any[] = [];
  let index = 0;

  while (index < lines.length) {
    const trimmed = lines[index].trim();
    if (!trimmed) {
      index += 1;
      continue;
    }

    if (trimmed.startsWith("### ")) {
      blocks.push({ type: "heading", text: trimmed.slice(4) });
      index += 1;
      continue;
    }

    if (trimmed.startsWith("- ")) {
      const items = [];
      while (index < lines.length && lines[index].trim().startsWith("- ")) {
        items.push(lines[index].trim().slice(2));
        index += 1;
      }
      blocks.push({ type: "list", items });
      continue;
    }

    if (trimmed.startsWith("|")) {
      const rows = [];
      while (index < lines.length && lines[index].trim().startsWith("|")) {
        const row = lines[index].trim();
        if (!row.includes("---")) rows.push(row.split("|").slice(1, -1).map((cell) => cell.trim()));
        index += 1;
      }
      blocks.push({ type: "table", rows });
      continue;
    }

    const paragraph = [trimmed];
    index += 1;
    while (index < lines.length) {
      const next = lines[index].trim();
      if (!next || next.startsWith("### ") || next.startsWith("- ") || next.startsWith("|")) break;
      paragraph.push(next);
      index += 1;
    }
    blocks.push({ type: "paragraph", text: paragraph.join(" ") });
  }

  return blocks;
}

export function getAsterNextActions(text: string) {
  if (text.includes("日報")) return ["下書きを保存", "内容を編集", "昨日の日報を見る"];
  if (text.includes("Inbox") || text.includes("OCR")) return ["DIBを開く", "OCR待機を見る", "関連記憶へ保存"];
  if (text.includes("記憶")) return ["Timelineで見る", "タグ整理", "関連メモを開く"];
  if (text.includes("Core") || text.includes("Ollama")) return ["状態画面へ", "ログを見る", "日報を作る"];
  return [];
}
