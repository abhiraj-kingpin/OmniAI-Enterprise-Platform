"use client";

import { motion, useMotionValue, useSpring } from "framer-motion";
import Link from "next/link";
import type { ReactNode, MouseEvent } from "react";

const SPRING = { stiffness: 200, damping: 15, mass: 0.2 };

/** A button/link that subtly follows the cursor within its own bounds
 * ("magnetic" hover) and glows on hover. Renders a Next.js <Link> when
 * `href` is given, a <button> otherwise. */
export default function MagneticButton({
  children,
  href,
  onClick,
  variant = "primary",
  className = "",
}: {
  children: ReactNode;
  href?: string;
  onClick?: () => void;
  variant?: "primary" | "glass";
  className?: string;
}) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, SPRING);
  const springY = useSpring(y, SPRING);

  function handleMove(e: MouseEvent<HTMLElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    x.set((e.clientX - rect.left - rect.width / 2) * 0.35);
    y.set((e.clientY - rect.top - rect.height / 2) * 0.35);
  }

  function handleLeave() {
    x.set(0);
    y.set(0);
  }

  const base =
    "group relative inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-medium transition-shadow duration-300";
  const styles =
    variant === "primary"
      ? "bg-white text-neutral-950 shadow-[0_0_0_0_rgba(255,255,255,0)] hover:shadow-[0_0_40px_4px_rgba(255,255,255,0.25)]"
      : "border border-white/15 bg-white/5 text-white backdrop-blur-md hover:border-white/30 hover:bg-white/10";

  const content = (
    <motion.span
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      style={{ x: springX, y: springY }}
      className={`${base} ${styles} ${className}`}
    >
      {children}
    </motion.span>
  );

  if (href) {
    const external = href.startsWith("http");
    if (external) {
      return (
        <a href={href} target="_blank" rel="noopener noreferrer" className="inline-block">
          {content}
        </a>
      );
    }
    return (
      <Link href={href} className="inline-block">
        {content}
      </Link>
    );
  }
  return (
    <button type="button" onClick={onClick} className="inline-block">
      {content}
    </button>
  );
}
