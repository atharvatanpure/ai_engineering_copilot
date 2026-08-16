import Link from "next/link";
import type { Repository } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  ready: "text-good border-good/30 bg-good/10",
  indexing: "text-accent border-accent/30 bg-accent/10",
  scanning: "text-accent border-accent/30 bg-accent/10",
  cloning: "text-accent border-accent/30 bg-accent/10",
  pending: "text-muted border-border bg-surface-alt",
  failed: "text-bad border-bad/30 bg-bad/10",
};

export default function RepositoryCard({ repo }: { repo: Repository }) {
  const topLanguages = Object.entries(repo.languages || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([lang]) => lang);

  return (
    <Link
      href={`/repository/${repo.id}`}
      className="gutter-line group block rounded-md border border-border bg-surface p-5 pr-5 transition hover:border-accent/50 hover:bg-surface-alt"
      data-line="{}"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="mono text-xs text-muted">{repo.owner}</p>
          <h3 className="text-lg font-semibold text-[#e6e8ef] group-hover:text-accent">
            {repo.name}
          </h3>
        </div>
        <span
          className={`mono rounded border px-2 py-0.5 text-[11px] uppercase tracking-wide ${
            STATUS_STYLES[repo.index_status] || STATUS_STYLES.pending
          }`}
        >
          {repo.index_status}
        </span>
      </div>

      <div className="mono mt-4 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
        <span>{repo.file_count} files</span>
        <span>{repo.line_count.toLocaleString()} lines</span>
        <span>{repo.chunk_count} chunks</span>
      </div>

      {topLanguages.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {topLanguages.map((lang) => (
            <span
              key={lang}
              className="mono rounded bg-surface-alt px-2 py-0.5 text-[11px] text-muted"
            >
              {lang}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
