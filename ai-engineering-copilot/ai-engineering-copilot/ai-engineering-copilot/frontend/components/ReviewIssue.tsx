import type { ReviewIssue as ReviewIssueType } from "@/types";
import SeverityBadge from "./SeverityBadge";

const CATEGORY_LABEL: Record<string, string> = {
  bug: "Bug",
  security: "Security",
  performance: "Performance",
  maintainability: "Maintainability",
  best_practice: "Best practice",
};

export default function ReviewIssue({ issue }: { issue: ReviewIssueType }) {
  return (
    <div className="gutter-line rounded-md border border-border bg-surface p-4 pr-4" data-line={issue.line ?? "—"}>
      <div className="flex flex-wrap items-center gap-2">
        <SeverityBadge severity={issue.severity} />
        <span className="mono rounded border border-border bg-surface-alt px-2 py-0.5 text-[11px] text-muted">
          {CATEGORY_LABEL[issue.category] || issue.category}
        </span>
        {issue.file && (
          <span className="mono text-[11px] text-muted">
            {issue.file}
            {issue.line ? `:${issue.line}` : ""}
          </span>
        )}
      </div>
      <h4 className="mt-2 font-medium text-[#e6e8ef]">{issue.title}</h4>
      <p className="mt-1 text-sm text-muted">{issue.description}</p>
      <p className="mt-2 rounded border border-border bg-surface-alt px-3 py-2 text-sm text-[#e6e8ef]">
        <span className="mono mr-1 text-accent">fix →</span>
        {issue.recommendation}
      </p>
    </div>
  );
}
