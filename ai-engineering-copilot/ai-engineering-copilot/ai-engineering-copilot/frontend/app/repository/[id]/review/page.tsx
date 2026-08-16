"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Repository, ReviewResponse, RepositoryFile } from "@/types";
import Sidebar from "@/components/Sidebar";
import ReviewIssue from "@/components/ReviewIssue";
import LoadingState from "@/components/LoadingState";
import EmptyState from "@/components/EmptyState";

export default function RepositoryReviewPage() {
  const { id } = useParams<{ id: string }>();
  const [repo, setRepo] = useState<Repository | null>(null);
  const [files, setFiles] = useState<RepositoryFile[]>([]);
  const [mode, setMode] = useState<"file" | "diff">("diff");
  const [selectedFile, setSelectedFile] = useState("");
  const [diffText, setDiffText] = useState("");
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getRepository(id).then(setRepo).catch(() => setRepo(null));
    api.listFiles(id).then(setFiles).catch(() => setFiles([]));
  }, [id]);

  async function handleReview() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload =
        mode === "file"
          ? { repository_id: id, file_path: selectedFile }
          : { repository_id: id, diff: diffText };
      const res = await api.review(payload);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Review failed.");
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = mode === "file" ? !!selectedFile : diffText.trim().length > 0;

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <p className="mono text-xs text-accent">{repo ? `${repo.owner}/${repo.name}` : ""}</p>
      <div className="mt-1 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-[#e6e8ef]">Code review</h1>
        <Sidebar repositoryId={id} />
      </div>

      <div className="mt-6 rounded-md border border-border bg-surface p-5">
        <div className="mono flex gap-1 rounded bg-surface-alt p-1 text-sm">
          <button
            onClick={() => setMode("diff")}
            className={`flex-1 rounded px-3 py-1.5 ${mode === "diff" ? "bg-accent text-white" : "text-muted"}`}
          >
            Paste diff / code
          </button>
          <button
            onClick={() => setMode("file")}
            className={`flex-1 rounded px-3 py-1.5 ${mode === "file" ? "bg-accent text-white" : "text-muted"}`}
          >
            Select repository file
          </button>
        </div>

        {mode === "diff" ? (
          <textarea
            value={diffText}
            onChange={(e) => setDiffText(e.target.value)}
            placeholder="Paste a diff or code snippet to review…"
            rows={10}
            className="mono mt-4 w-full rounded border border-border bg-surface-alt p-3 text-sm text-[#e6e8ef] outline-none focus:border-accent"
          />
        ) : (
          <select
            value={selectedFile}
            onChange={(e) => setSelectedFile(e.target.value)}
            className="mono mt-4 w-full rounded border border-border bg-surface-alt p-2.5 text-sm text-[#e6e8ef] outline-none focus:border-accent"
          >
            <option value="">Select a file…</option>
            {files.map((f) => (
              <option key={f.file_path} value={f.file_path}>
                {f.file_path}
              </option>
            ))}
          </select>
        )}

        <button
          onClick={handleReview}
          disabled={!canSubmit || loading}
          className="mono mt-4 rounded bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-soft disabled:opacity-40"
        >
          {loading ? "Reviewing…" : "Run AI review"}
        </button>
        {error && <p className="mt-2 text-sm text-bad">{error}</p>}
      </div>

      <div className="mt-8">
        {loading && <LoadingState label="Analyzing code for bugs, security, and quality issues" />}
        {result && (
          <>
            <div className="gutter-line rounded-md border border-border bg-surface p-4 pr-4" data-line="!">
              <p className="mono text-xs uppercase tracking-wide text-muted">Summary</p>
              <p className="mt-1 text-sm text-[#e6e8ef]">{result.summary}</p>
            </div>
            <div className="mt-4 space-y-3">
              {result.issues.length === 0 ? (
                <EmptyState title="No issues found" description="The AI reviewer found nothing worth flagging." />
              ) : (
                result.issues.map((issue, idx) => <ReviewIssue key={idx} issue={issue} />)
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
