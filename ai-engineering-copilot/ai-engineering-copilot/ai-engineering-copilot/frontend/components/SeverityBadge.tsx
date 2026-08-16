import type { Severity } from "@/types";

const STYLES: Record<Severity, string> = {
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  low: "bg-sky-500/15 text-sky-400 border-sky-500/30",
  info: "bg-slate-500/15 text-slate-300 border-slate-500/30",
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`mono rounded border px-2 py-0.5 text-[11px] uppercase tracking-wide ${STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}
