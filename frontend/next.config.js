/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  // Disable automatic rmdir of .next on Windows/OneDrive to prevent EPERM lock errors
  cleanDistDir: false,
};

module.exports = nextConfig;
