import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "OmniAI · Enterprise Platform",
  description: "Sixteen AI modules — chat, RAG, vision, speech, and more — in one platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-neutral-950 text-neutral-100">{children}</body>
    </html>
  );
}
