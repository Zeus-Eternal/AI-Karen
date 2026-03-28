import path from 'path';
import type {NextConfig} from 'next';

const backendBaseUrl =
  process.env.KAREN_BACKEND_URL ||
  'http://api:8000';

const allowedDevOrigins = [
  'localhost',
  '127.0.0.1',
  '172.21.0.11',
  '172.21.0.12',
];

const nextConfig: NextConfig = {
  /* config options here */
  outputFileTracingRoot: path.resolve(__dirname, '../..'),
  allowedDevOrigins,
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendBaseUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
