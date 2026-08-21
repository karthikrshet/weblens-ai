/** @type {import('next').NextConfig} */
const backendUrl =
  process.env.BACKEND_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000/api/v1";

const normalizedDestination = `${backendUrl.replace(/\/+$/, "").replace(/\/api\/v1$/, "")}/api/v1/:path*`;

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: normalizedDestination,
      },
    ];
  },
};

module.exports = nextConfig;

