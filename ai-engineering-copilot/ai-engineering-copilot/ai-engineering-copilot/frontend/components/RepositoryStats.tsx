import type { Repository } from "@/types";

export default function RepositoryStats({ repo }: { repo: Repository }) {
  const stats: { label: string; value: string }[] = [
    { label: "files", value: repo.file_count.toLocaleString() },
    { label: "lines of code", value: repo.line_count.toLocaleString() },
    { label: "indexed chunks", value: repo.chunk_count.toLocaleString() },
    { label: "languages", value: String(Object.keys(repo.languages || {}).length) },
  ];

  return (
    <div className="grid grid-cols-2 gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-4">
      {stats.map((s, i) => (
        <div key={s.label} className="gutter-line bg-surface px-5 py-4" data-line={String(i + 1).padStart(2, "0")}>
          <p className="text-2xl font-semibold text-[#e6e8ef]">{s.value}</p>
          <p className="mono mt-1 text-xs text-muted">{s.label}</p>
        </div>
      ))}
    </div>
  );
}
