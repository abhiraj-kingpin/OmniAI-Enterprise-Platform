"use client";

import { motion, type Variants } from "framer-motion";
import type { ReactNode } from "react";

const VARIANTS: Variants = {
  hidden: { opacity: 0, y: 32, filter: "blur(8px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] },
  },
};

/** Fades, lifts, and un-blurs children into view the first time they cross
 * the viewport — the "blur to clear" reveal used throughout the landing
 * page. `delay` staggers siblings; `once` (default true) keeps it from
 * re-triggering on scroll-back. */
export default function Reveal({
  children,
  delay = 0,
  className,
  once = true,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  once?: boolean;
}) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount: 0.3 }}
      variants={VARIANTS}
      transition={{ delay }}
    >
      {children}
    </motion.div>
  );
}
