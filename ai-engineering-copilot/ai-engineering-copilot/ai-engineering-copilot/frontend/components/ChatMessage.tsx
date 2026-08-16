"use client";

import type { ChatMessage as ChatMessageType, SourceCitation as SourceCitationType } from "@/types";
import SourceCitation from "./SourceCitation";

export default function ChatMessage({
  message,
  onOpenSource,
}: {
  message: ChatMessageType;
  onOpenSource?: (source: SourceCitationType) => void;
}) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[80%] ${isUser ? "" : "w-full"}`}>
        <div
          className={
            isUser
              ? "rounded-md bg-accent px-4 py-2.5 text-sm text-white"
              : "gutter-line rounded-md border border-border bg-surface px-4 py-3 pr-4 text-sm text-[#e6e8ef]"
          }
          data-line={isUser ? undefined : "AI"}
        >
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        </div>

        {!isUser && message.sources.length > 0 && (
          <div className="mt-2 space-y-1.5">
            <p className="mono text-[11px] uppercase tracking-wide text-muted">Sources</p>
            <div className="grid gap-1.5 sm:grid-cols-2">
              {message.sources.map((source, idx) => (
                <SourceCitation key={idx} source={source} onOpen={onOpenSource} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
