"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Repository, RepositoryFile } from "@/types";
import Sidebar from "@/components/Sidebar";
import RepositoryStats from "@/components/RepositoryStats";
import LoadingState from "@/components/LoadingState";
import EmptyState from "@/components/EmptyState";

export default function RepositoryOverviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [repo, setRepo] = useState<Repository | null>(null);
  const [files, setFiles] = useState<RepositoryFile[] | null>(null);
  const [indexing, setIndexing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const r = await api.getRepository(id);
      setRepo(r);
      if (r.index_status === "ready") {
        setFiles(await api.listFiles(id));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load repository.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleIndex() {
    setIndexing(true);
    setError(null);
    try {
      const r = await api.indexRepository(id);
      setRepo(r);
      setFiles(await api.listFiles(id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Indexing failed.");
    } finally {
      setIndexing(false);
    }
  }

  if (!repo) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-10">
        {error ? <p className="text-sm text-bad">{error}</p> : <LoadingState label="Loading repository" />}
      </div>
    );
  }

  const canChat = repo.index_status === "ready";

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <p className="mono text-xs text-accent">
        {repo.owner}/{repo.name}
      </p>
      <div className="mt-1 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-[#e6e8ef]">{repo.name}</h1>
        <Sidebar repositoryId={id} />
      </div>

      <div className="mt-6">
        <RepositoryStats repo={repo} />
      </div>

      {repo.index_status === "failed" && (
        <div className="mt-4 rounded-md border border-bad/30 bg-bad/10 p-4 text-sm text-bad">
          {repo.error_message || "Something went wrong processing this repository."}
        </div>
      )}

      <div className="mt-6 flex flex-wrap gap-3">
        <Link
          href={canChat ? `/repository/${id}/chat` : "#"}
          aria-disabled={!canChat}
          className={`mono rounded px-4 py-2 text-sm font-medium transition ${
            canChat
              ? "bg-accent text-white hover:bg-accent-soft"
              : "cursor-not-allowed bg-surface-alt text-muted"
          }`}
        >
          Ask AI
        </Link>
        <Link
          href={`/repository/${id}/review`}
          className="mono rounded border border-border bg-surface px-4 py-2 text-sm font-medium text-[#e6e8ef] transition hover:border-accent/50"
        >
          Code review
        </Link>
        <button
          onClick={handleIndex}
          disabled={indexing}
          className="mono rounded border border-border bg-surface px-4 py-2 text-sm font-medium text-[#e6e8ef] transition hover:border-accent/50 disabled:opacity-40"
        >
          {indexing ? "Indexing…" : repo.index_status === "ready" ? "Re-index" : "Index repository"}
        </button>
      </div>

      {error && <p className="mt-3 text-sm text-bad">{error}</p>}

      <div className="mt-10">
        <p className="mono mb-3 text-xs uppercase tracking-wide text-muted">Files</p>
        {!files && repo.index_status !== "ready" && (
          <EmptyState
            title="Not indexed yet"
            description="Index this repository to enable AI chat, source citations, and the file list below."
          />
        )}
        {files && files.length > 0 && (
          <div className="scrollbar-thin max-h-96 overflow-auto rounded-md border border-border bg-surface">
            <table className="mono w-full text-left text-xs">
              <thead className="sticky top-0 bg-surface-alt text-muted">
                <tr>
                  <th className="px-4 py-2 font-normal">Path</th>
                  <th className="px-4 py-2 font-normal">Language</th>
                  <th className="px-4 py-2 font-normal">Lines</th>
                  <th className="px-4 py-2 font-normal">Indexed</th>
                </tr>
              </thead>
              <tbody>
                {files.map((f) => (
                  <tr key={f.file_path} className="border-t border-border">
                    <td className="px-4 py-2 text-[#e6e8ef]">{f.file_path}</td>
                    <td className="px-4 py-2 text-muted">{f.language || "—"}</td>
                    <td className="px-4 py-2 text-muted">{f.line_count}</td>
                    <td className="px-4 py-2">
                      <span className={f.indexed ? "text-good" : "text-muted"}>
                        {f.indexed ? "yes" : "no"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
