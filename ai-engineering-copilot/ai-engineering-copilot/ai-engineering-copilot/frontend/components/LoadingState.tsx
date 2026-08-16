export default function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-10 text-sm text-muted">
      <span className="mono h-2 w-2 animate-pulse rounded-full bg-accent" />
      <span className="mono">{label}…</span>
    </div>
  );
}
