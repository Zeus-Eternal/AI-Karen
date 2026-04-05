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

  webpack: (config) => {
    const fs = require('fs');

    // 1. Ensure require.context('@/plugins', ...) doesn't fail at build time
    //    if the user hasn't installed any plugins. In Docker, creating folders
    //    can fail due to permissions, so we gracefully alias it instead.
    const pluginsDir = path.resolve(__dirname, 'src/plugins');
    if (!fs.existsSync(pluginsDir)) {
      if (!config.resolve) config.resolve = {};
      if (!config.resolve.alias) config.resolve.alias = {};
      
      // Alias to a directory that definitely exists so require.context succeeds.
      // The regex /ui\/.*PluginPage\.(tsx|jsx)$/ won't match anything here anyway.
      config.resolve.alias['@/plugins'] = path.resolve(__dirname, 'src/plugin_host');
      console.log('🧩 [PluginLoader] src/plugins missing, aliasing to plugin_host for safe require.context');
    }

    // 2. Gracefully handle optional legacy plugins that may not be installed.
    //    If the file doesn't exist, we alias the path to false so Webpack 
    //    ignores it instead of throwing a "Module not found" error that stalls the app.
    const legacyDataConnector = path.resolve(__dirname, 'src/plugins/data_connector/ui/DataConnectorPluginPage');
    if (!fs.existsSync(`${legacyDataConnector}.tsx`) && !fs.existsSync(`${legacyDataConnector}.jsx`)) {
      if (!config.resolve) config.resolve = {};
      if (!config.resolve.alias) config.resolve.alias = {};
      config.resolve.alias['@/plugins/data_connector/ui/DataConnectorPluginPage'] = path.resolve(__dirname, 'src/plugin_host/empty-plugin.tsx');
      console.log('🧩 [PluginLoader] karen-data-connector not strictly found, marked as optional.');
    }

    return config;
  },
};

export default nextConfig;
