import path from "node:path";
import fs from "node:fs";
import type { NextConfig } from "next";

const repoRoot = path.join(__dirname, "../..");
const repoEnvPath = path.join(repoRoot, ".env");

if (fs.existsSync(repoEnvPath)) {
  const repoEnv = fs.readFileSync(repoEnvPath, "utf8");
  for (const rawLine of repoEnv.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }

    const separatorIndex = line.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }

    const key = line.slice(0, separatorIndex).trim();
    const value = line
      .slice(separatorIndex + 1)
      .trim()
      .replace(/^['"]|['"]$/g, "");

    if (key && process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}

const nextConfig: NextConfig = {
  transpilePackages: ["@soil/shared-types"],
  outputFileTracingRoot: repoRoot,
};

export default nextConfig;
