/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (process.env.BACKEND_API_URL) {
      const backend = process.env.BACKEND_API_URL.replace(/\/+$/, "").replace(/\/api\/v1$/, "");
      return [
        {
          source: "/api/v1/:path*",
          destination: `${backend}/api/v1/:path*`,
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;

