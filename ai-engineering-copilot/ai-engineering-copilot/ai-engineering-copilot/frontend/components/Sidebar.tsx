"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = (id: string) => [
  { href: `/repository/${id}`, label: "Overview" },
  { href: `/repository/${id}/chat`, label: "Ask AI" },
  { href: `/repository/${id}/review`, label: "Code review" },
];

export default function Sidebar({ repositoryId }: { repositoryId: string }) {
  const pathname = usePathname();

  return (
    <nav className="mono flex gap-1 rounded-md border border-border bg-surface p-1 text-sm">
      {LINKS(repositoryId).map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`rounded px-3 py-1.5 transition ${
              active ? "bg-accent text-white" : "text-muted hover:text-[#e6e8ef]"
            }`}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
