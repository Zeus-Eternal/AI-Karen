import path from 'path';
import type {NextConfig} from 'next';

// Determine the backend URL based on the environment
const backendBaseUrl = process.env.KAREN_BACKEND_URL || 'http://localhost:8000';
const isDocker = process.env.KAREN_DOCKER === 'true';

console.log(`Backend URL: ${backendBaseUrl}, isDocker: ${isDocker}`);

const allowedDevOrigins = [
  'localhost',
  '127.0.0.1',
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
