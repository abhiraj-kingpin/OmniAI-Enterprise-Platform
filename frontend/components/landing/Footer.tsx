import Link from "next/link";

import { MODULES } from "@/lib/modules";

const COLUMNS = [
  { title: "Modules", items: MODULES.slice(0, 5).map((m) => ({ href: m.href, label: m.name })) },
  {
    title: "More modules",
    items: MODULES.slice(5, 10).map((m) => ({ href: m.href, label: m.name })),
  },
  {
    title: "Platform",
    items: [
      { href: "/dashboard", label: "Dashboard" },
      { href: "#architecture", label: "Architecture" },
      { href: "#get-started", label: "Get Started" },
      { href: "#faq", label: "FAQ" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-white/10 py-16">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
          <div className="col-span-2 sm:col-span-1">
            <p className="text-sm font-semibold text-white">OmniAI</p>
            <p className="mt-2 text-xs leading-relaxed text-neutral-500">
              A FastAPI + Next.js platform covering sixteen AI modules behind one backend.
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <p className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
                {col.title}
              </p>
              <ul className="mt-3 space-y-2">
                {col.items.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className="text-xs text-neutral-500 transition-colors hover:text-neutral-300"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-6 sm:flex-row">
          <p className="text-xs text-neutral-600">OmniAI Enterprise Platform</p>
          <a
            href="https://github.com/abhiraj-kingpin/OmniAI-Enterprise-Platform"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-neutral-500 hover:text-neutral-300"
          >
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
