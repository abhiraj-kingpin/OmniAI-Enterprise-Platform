import { fileURLToPath } from "node:url";
import { dirname } from "node:path";

const projectRoot = dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Pins workspace root to this project explicitly — without it, Next.js
  // infers the root by walking up for the nearest lockfile, which picks up
  // an unrelated one outside this repository on some machines.
  outputFileTracingRoot: projectRoot,
};

export default nextConfig;
