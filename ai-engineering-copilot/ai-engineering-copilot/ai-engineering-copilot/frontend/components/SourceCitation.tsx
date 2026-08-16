"use client";

import type { SourceCitation as SourceCitationType } from "@/types";

export default function SourceCitation({
  source,
  onOpen,
}: {
  source: SourceCitationType;
  onOpen?: (source: SourceCitationType) => void;
}) {
  return (
    <button
      onClick={() => onOpen?.(source)}
      className="mono flex w-full flex-col items-start gap-0.5 rounded border border-border bg-surface-alt px-3 py-2 text-left text-xs transition hover:border-accent/50"
    >
      <span className="text-[#e6e8ef]">{source.file_path}</span>
      <span className="text-muted">
        lines {source.start_line}–{source.end_line}
        {source.symbol ? ` · ${source.symbol}` : ""}
      </span>
    </button>
  );
}
