"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MODULES } from "@/lib/modules";

const NAV_ITEMS = [{ href: "/dashboard", label: "Dashboard" }, ...MODULES.map((m) => ({ href: m.href, label: m.name }))];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="flex h-screen w-56 shrink-0 flex-col border-r border-neutral-800 bg-neutral-950 p-3">
      <Link href="/" className="mb-4 block rounded-md px-2 py-2 hover:bg-neutral-900">
        <p className="text-sm font-bold text-neutral-100">OmniAI</p>
        <p className="text-[11px] text-neutral-500">Enterprise Platform</p>
      </Link>
      <div className="flex-1 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-md px-3 py-1.5 text-[13px] transition-colors ${
                active
                  ? "bg-blue-600/20 text-blue-300"
                  : "text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
