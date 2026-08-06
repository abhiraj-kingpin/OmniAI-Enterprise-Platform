"use client";

import { useEffect } from "react";
import Lenis from "lenis";
import gsap from "gsap";

/** Wires Lenis smooth scrolling in, driven by GSAP's own ticker rather than
 * a separate requestAnimationFrame loop — the standard Lenis+GSAP
 * integration, so ScrollTrigger's scroll-linked animations elsewhere see
 * the same smoothed scroll position Lenis is rendering instead of two
 * competing frame loops drifting out of sync. */
export default function SmoothScroll() {
  useEffect(() => {
    const lenis = new Lenis({ duration: 1.1, smoothWheel: true });

    function onTick(time: number) {
      lenis.raf(time * 1000);
    }
    gsap.ticker.add(onTick);
    gsap.ticker.lagSmoothing(0);

    import("gsap/ScrollTrigger").then(({ ScrollTrigger }) => {
      lenis.on("scroll", ScrollTrigger.update);
    });

    return () => {
      gsap.ticker.remove(onTick);
      lenis.destroy();
    };
  }, []);

  return null;
}
