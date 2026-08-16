import Link from "next/link";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="mono text-xs text-muted">01</span>
          <span className="font-semibold tracking-tight text-[#e6e8ef]">
            AI Engineering <span className="text-accent">Copilot</span>
          </span>
        </Link>
        <nav className="mono flex items-center gap-6 text-sm text-muted">
          <Link href="/dashboard" className="transition hover:text-[#e6e8ef]">
            dashboard
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="transition hover:text-[#e6e8ef]"
          >
            docs
          </a>
        </nav>
      </div>
    </header>
  );
}
