import type { NextConfig } from "next";

// Where the Next server proxies /api/*. Read at build time; Docker Compose
// passes http://backend:8000 as a build arg.
const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
