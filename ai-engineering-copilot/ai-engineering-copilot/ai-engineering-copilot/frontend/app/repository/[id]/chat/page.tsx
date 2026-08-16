"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Repository } from "@/types";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import LoadingState from "@/components/LoadingState";
import EmptyState from "@/components/EmptyState";

export default function RepositoryChatPage() {
  const { id } = useParams<{ id: string }>();
  const [repo, setRepo] = useState<Repository | null>(null);

  useEffect(() => {
    api.getRepository(id).then(setRepo).catch(() => setRepo(null));
  }, [id]);

  if (!repo) return <div className="mx-auto max-w-6xl px-6 py-10"><LoadingState label="Loading" /></div>;

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <p className="mono text-xs text-accent">
        {repo.owner}/{repo.name}
      </p>
      <div className="mt-1 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-[#e6e8ef]">Ask AI</h1>
        <Sidebar repositoryId={id} />
      </div>

      <div className="mt-6">
        {repo.index_status === "ready" ? (
          <ChatWindow repositoryId={id} />
        ) : (
          <EmptyState
            title="Repository not indexed"
            description="Go to the overview tab and index this repository before asking questions."
          />
        )}
      </div>
    </div>
  );
}
