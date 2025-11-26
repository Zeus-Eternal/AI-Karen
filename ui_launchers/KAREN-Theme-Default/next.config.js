/** @type {import('next').NextConfig} */
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const nextConfig = {
  // Basic configuration to fix React Client Manifest issues
  reactStrictMode: false,
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Fix for missing chunk issue in development
  images: {
    unoptimized: true
  },
  experimental: {
    // Disable all experimental features that might cause manifest issues
  },
  // Output configuration for static export (temporarily disabled for development)
  // output: 'export',
  // Skip trailing slash redirect for static export
  // trailingSlash: false,
  // Disable server-side features for static export
  generateBuildId: async () => {
    return 'static-build';
  },
  webpack: (config, { isServer, dev }) => {
    // Basic webpack configuration
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        path: false,
        crypto: false,
        dns: false,
        pg: false,
      };
    }

    // Fix module resolution for CommonJS/ESM hybrid packages
    config.module.rules.push({
      test: /\.m?js$/,
      resolve: {
        fullySpecified: false,
      },
    });

    // Improve module resolution for better client manifest generation
    config.resolve.extensions = ['.ts', '.tsx', '.js', '.jsx', '.json'];

    // Fix server-side chunk loading issue
    if (isServer) {
      // Override the webpack runtime to fix chunk loading on server side
      config.resolve.alias = {
        ...config.resolve.alias,
        // Fix the chunk loading path resolution
        './chunks': path.join(__dirname, '.next/server/chunks'),
      };
      
      // Ensure proper chunk loading in server environment
      config.optimization = {
        ...config.optimization,
        // Disable code splitting for server builds to avoid chunk loading issues
        splitChunks: dev ? false : {
          ...config.optimization?.splitChunks,
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            // Create a single chunk for all server code
            server: {
              name: 'server',
              chunks: 'all',
              priority: 10,
            },
          },
        },
      };
    }

    return config;
  },
};

export default nextConfig;