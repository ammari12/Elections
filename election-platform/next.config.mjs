/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  basePath: "/Elections",
  assetPrefix: "/Elections/",
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
};

export default nextConfig;
