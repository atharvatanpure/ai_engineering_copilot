"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Repository } from "@/types";
import RepositoryCard from "@/components/RepositoryCard";
import EmptyState from "@/components/EmptyState";
import LoadingState from "@/components/LoadingState";

export default function DashboardPage() {
  const router = useRouter();
  const [repos, setRepos] = useState<Repository[] | null>(null);
  const [url, setUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadRepos() {
    try {
      setRepos(await api.listRepositories());
    } catch {
      setError("Could not load repositories. Is the backend running?");
    }
  }

  useEffect(() => {
    loadRepos();
  }, []);

  async function handleImport() {
    if (!url.trim() || importing) return;
    setImporting(true);
    setError(null);
    try {
      const repo = await api.createRepository(url.trim());
      router.push(`/repository/${repo.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to import repository.");
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="mono text-xs text-accent">// dashboard</p>
          <h1 className="mt-1 text-2xl font-semibold text-[#e6e8ef]">Repositories</h1>
        </div>
      </div>

      <div className="mt-6 rounded-md border border-border bg-surface p-5">
        <label className="mono text-xs text-muted">Import a public GitHub repository</label>
        <div className="mt-2 flex gap-2">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleImport()}
            placeholder="https://github.com/owner/repo"
            className="mono flex-1 rounded border border-border bg-surface-alt px-3 py-2 text-sm text-[#e6e8ef] outline-none focus:border-accent"
          />
          <button
            onClick={handleImport}
            disabled={importing || !url.trim()}
            className="mono whitespace-nowrap rounded bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-soft disabled:opacity-40"
          >
            {importing ? "Importing…" : "Import repository"}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-bad">{error}</p>}
      </div>

      <div className="mt-8">
        {repos === null && <LoadingState label="Loading repositories" />}
        {repos?.length === 0 && (
          <EmptyState
            title="No repositories yet"
            description="Import a public GitHub repository above to get started."
          />
        )}
        {repos && repos.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {repos.map((repo) => (
              <RepositoryCard key={repo.id} repo={repo} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
