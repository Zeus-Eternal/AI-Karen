import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizeCss: true,
    // This is needed to avoid conflicts between App Router and Pages Router
    serverComponentsExternalPackages: [],
  },
  webpack: (config) => {
    config.resolve.alias['@root-config'] = path.resolve(__dirname, '../../config');
    config.resolve.alias['@root-config/permissions.json'] = path.resolve(__dirname, '../../config/permissions.json');
    return config;
  },
  // Ensure the pages directory is properly recognized
  pageExtensions: ['tsx', 'ts', 'jsx', 'js'],
};

export default nextConfig;
