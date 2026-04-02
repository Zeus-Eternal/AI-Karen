import path from 'path';
import os from 'os';
import type {NextConfig} from 'next';

const isDocker = process.env.KAREN_DOCKER === 'true' || 
                 process.env.IS_DOCKER === 'true' || 
                 process.env.HOSTNAME?.includes('api') || 
                 process.env.HOSTNAME?.includes('web');

let BACKEND_URL = process.env.KAREN_BACKEND_URL || process.env.BACKEND_URL || '';

if (isDocker) {
    BACKEND_URL = 'http://api:8000';
} else if (!BACKEND_URL) {
    BACKEND_URL = 'http://localhost:8000';
}

const backendBaseUrl = BACKEND_URL.replace(/\/$/, '');

console.log('🚀 Next.js Configuration:');
console.log(`- isDocker: ${isDocker}`);
console.log(`- RESOLVED backendBaseUrl: ${backendBaseUrl}`);

const devOriginCandidates = [
  'localhost',
  '127.0.0.1',
  'api',
  'web',
  'host.docker.internal',
  process.env.HOSTNAME,
  process.env.NEXT_PUBLIC_APP_URL,
  process.env.KAREN_APP_URL,
  process.env.APP_URL,
];

const privateInterfaceHosts = Object.values(os.networkInterfaces())
  .flat()
  .filter((address): address is NonNullable<typeof address> => Boolean(address))
  .filter((address) => address.family === 'IPv4' && !address.internal)
  .map((address) => address.address);

const allowedDevOrigins = Array.from(
  new Set(
    devOriginCandidates
      .filter((value): value is string => Boolean(value))
      .flatMap((value) => {
        try {
          const parsed = new URL(value);
          return [value, parsed.hostname];
        } catch {
          return [value];
        }
      })
      // Allow the actual container / LAN IPv4 hosts that Next may advertise
      // for HMR in development.
      .concat(privateInterfaceHosts),
  ),
);

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
    // API proxying is handled by App Router route handlers under src/app/api,
    // including a catch-all proxy route. Rewriting /api/* here can create
    // self-referential loops when BACKEND_URL matches the Next dev origin.
    console.log('📡 [Rewrites] No /api rewrite configured; using app/api route handlers');
    return [];
  },
};

export default nextConfig;
