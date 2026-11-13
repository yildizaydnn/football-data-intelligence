import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker imajı için yalnızca çalışmaya gereken dosyaları .next/standalone'a toplar.
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
  images: {
    // Takım/lig logoları API-Football CDN'inden gelir.
    remotePatterns: [{ protocol: "https", hostname: "media.api-sports.io" }],
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
