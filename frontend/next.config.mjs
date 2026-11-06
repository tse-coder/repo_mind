/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  compress: false,
  async rewrites() {
    return [
      {
        source: '/api/((?!auth).*)',
        destination: 'http://localhost:8000/api/$1',
      },
    ];
  },
};

export default nextConfig;
