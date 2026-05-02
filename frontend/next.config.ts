/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["shared"],
  experimental: {
    optimizePackageImports: ["shared"],
  },
};

module.exports = nextConfig;
