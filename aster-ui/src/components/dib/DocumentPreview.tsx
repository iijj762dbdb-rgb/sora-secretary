import React, { useEffect, useState } from "react";
import { FileText } from "lucide-react";

export function DocumentPreview({ fileUrl, fileType, fileName }: any) {
  const [loading, setLoading] = useState(true);
  const isAppleMobile = typeof navigator !== "undefined" && /iPhone|iPad|iPod/.test(navigator.userAgent || "");
  
  useEffect(() => setLoading(true), [fileUrl, fileType]);

  if (fileType === "image") {
    return (
      <div className="relative flex h-full w-full items-center justify-center bg-black/10 p-3">
        {loading && <PreviewLoading />}
        <img src={fileUrl} alt={`\${fileName} preview`} onLoad={() => setLoading(false)} onError={() => setLoading(false)} className="max-h-full max-w-full rounded-2xl object-contain shadow-2xl transition-opacity duration-300" style={{ opacity: loading ? 0 : 1 }} />
      </div>
    );
  }

  if (fileType === "pdf") {
    if (isAppleMobile) return <PdfFallback fileUrl={fileUrl} fileName={fileName} reason="iPhone / iPad では埋め込みPDFが不安定なため、別タブ確認を優先します。" />;
    return (
      <div className="relative h-full w-full bg-black/5 p-3">
        {loading && <PreviewLoading />}
        <object data={`\${fileUrl || "about:blank"}#toolbar=0&navpanes=0`} type="application/pdf" className="h-full w-full rounded-2xl border border-white/10 bg-white/5" onLoad={() => setLoading(false)}>
          <PdfFallback fileUrl={fileUrl} fileName={fileName} reason="この環境ではPDFプレビューを表示できませんでした。" />
        </object>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center text-slate-500">
      <FileText className="h-16 w-16 opacity-25" />
      <p className="text-sm">このファイル形式のプレビューにはまだ対応していません。</p>
      <p className="text-xs text-slate-500">{fileName}</p>
    </div>
  );
}

function PreviewLoading() {
  return <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#0a0f1d]/50 backdrop-blur-sm"><div className="h-9 w-9 animate-spin rounded-full border-2 border-cyan-300/20 border-t-cyan-300" /></div>;
}

function PdfFallback({ fileUrl, fileName, reason }: any) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-6 text-center text-slate-400">
      <FileText className="h-16 w-16 opacity-30" />
      <div><p className="text-sm font-medium text-slate-300">PDFプレビュー</p><p className="mt-1 text-xs leading-5 text-slate-500">{reason}</p><p className="mt-2 text-xs text-slate-500">{fileName}</p></div>
      <a href={fileUrl || "about:blank"} target="_blank" rel="noopener noreferrer" className="rounded-xl bg-cyan-500/20 px-4 py-2 text-xs font-medium text-cyan-300 hover:bg-cyan-500/30">別タブで開く</a>
    </div>
  );
}
