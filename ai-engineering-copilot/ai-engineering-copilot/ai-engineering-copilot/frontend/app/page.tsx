import Link from "next/link";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-24">
      <p className="mono text-xs text-accent">// repository-aware AI</p>
      <h1 className="mt-3 text-4xl font-semibold leading-tight tracking-tight text-[#e6e8ef] sm:text-5xl">
        An AI engineering assistant<br />that understands your entire codebase.
      </h1>
      <p className="mt-5 max-w-xl text-muted">
        Import a public GitHub repository, index it with code-aware RAG, ask questions
        grounded in real source citations, and run an AI code review — all in one
        developer-focused workspace.
      </p>
      <div className="mt-8 flex gap-3">
        <Link
          href="/dashboard"
          className="mono rounded bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:bg-accent-soft"
        >
          Open dashboard
        </Link>
      </div>

      <div className="mt-16 grid gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-3">
        {[
          { n: "01", t: "Index", d: "Structure-aware chunking + embeddings stored in ChromaDB." },
          { n: "02", t: "Ask", d: "Questions answered strictly from retrieved code, with citations." },
          { n: "03", t: "Review", d: "Structured AI review across bugs, security, and performance." },
        ].map((f) => (
          <div key={f.n} className="gutter-line bg-surface px-5 py-5" data-line={f.n}>
            <p className="font-medium text-[#e6e8ef]">{f.t}</p>
            <p className="mt-1 text-sm text-muted">{f.d}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
