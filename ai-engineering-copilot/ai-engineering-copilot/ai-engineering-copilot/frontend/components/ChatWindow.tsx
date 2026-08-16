"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ChatMessage as ChatMessageType, SourceCitation as SourceCitationType } from "@/types";
import ChatMessage from "./ChatMessage";
import CodeViewer from "./CodeViewer";
import LoadingState from "./LoadingState";

export default function ChatWindow({ repositoryId }: { repositoryId: string }) {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openSource, setOpenSource] = useState<{ source: SourceCitationType; content: string } | null>(
    null
  );

  async function handleSend() {
    const question = input.trim();
    if (!question || sending) return;

    setInput("");
    setError(null);
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: question, sources: [] },
    ]);
    setSending(true);

    try {
      const res = await api.chat(repositoryId, question, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong asking the AI.");
    } finally {
      setSending(false);
    }
  }

  async function handleOpenSource(source: SourceCitationType) {
    try {
      const res = await api.getFileContent(repositoryId, source.file_path);
      setOpenSource({ source, content: res.content });
    } catch {
      setError("Could not load that source file.");
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr,420px]">
      <div className="flex h-[70vh] flex-col rounded-md border border-border bg-surface">
        <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto p-5">
          {messages.length === 0 && (
            <p className="mono text-sm text-muted">
              Ask a question about this repository — e.g. &quot;How does authentication work?&quot;
            </p>
          )}
          {messages.map((m) => (
            <ChatMessage key={m.id} message={m} onOpenSource={handleOpenSource} />
          ))}
          {sending && <LoadingState label="Retrieving context and generating an answer" />}
          {error && <p className="text-sm text-bad">{error}</p>}
        </div>
        <div className="flex gap-2 border-t border-border p-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about this codebase…"
            className="mono flex-1 rounded border border-border bg-surface-alt px-3 py-2 text-sm text-[#e6e8ef] outline-none focus:border-accent"
          />
          <button
            onClick={handleSend}
            disabled={sending || !input.trim()}
            className="mono rounded bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-soft disabled:opacity-40"
          >
            Ask
          </button>
        </div>
      </div>

      <div className="h-[70vh] overflow-hidden">
        {openSource ? (
          <CodeViewer
            filePath={openSource.source.file_path}
            content={openSource.content}
            highlightStart={openSource.source.start_line}
            highlightEnd={openSource.source.end_line}
          />
        ) : (
          <div className="flex h-full items-center justify-center rounded-md border border-dashed border-border text-center text-sm text-muted">
            Click a source citation to preview the code
          </div>
        )}
      </div>
    </div>
  );
}
