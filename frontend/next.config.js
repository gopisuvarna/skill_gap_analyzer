/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: process.env.DOCKER_BUILD ? 'standalone' : undefined,
};

module.exports = nextConfig;
