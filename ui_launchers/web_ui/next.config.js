let withBundleAnalyzer = (config) => config;
try {
  if (process.env.ANALYZE === 'true') {
    // Lazily require only when analyzing to avoid dev-time module errors
    const analyzer = require('@next/bundle-analyzer');
    withBundleAnalyzer = analyzer({ enabled: true, openAnalyzer: false });
  }
} catch (e) {
  // Analyzer not installed; skip without failing dev
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Explicitly set the root directory to prevent Next.js from looking at parent directories
  experimental: {
    // Other experimental features can go here
  },
  
  // Force Next.js to use this directory as the workspace root
  distDir: '.next',
  
  // Explicitly set the output file tracing root to prevent workspace detection issues
  outputFileTracingRoot: __dirname,
  
  // TypeScript configuration
  typescript: {
    // Enable type checking during build for better code quality
    ignoreBuildErrors: false,
  },

  // ESLint configuration
  eslint: {
    // Enable ESLint during production builds for code quality
    ignoreDuringBuilds: false,
    // Only ignore specific rules if needed
    dirs: ['src'],
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' data: https:; connect-src 'self' http://localhost:* http://127.0.0.1:* https: wss: ws://localhost:* ws://127.0.0.1:*;",
          },
        ],
      },
    ];
  },
  
  webpack: (config, { isServer, dev }) => {
    if (isServer) {
      // Node's runtime expects server chunks to live alongside webpack-runtime.js
      // so we force id-based filenames to keep them flat (e.g. "5611.js").
      config.output = {
        ...config.output,
        chunkFilename: '[id].js',
        hotUpdateChunkFilename: '[id].[fullhash].hot-update.js',
      };
    }

    // Handle ES modules properly
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        path: false,
        crypto: false,
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
    
    // Ensure proper module format handling
    config.experiments = {
      ...config.experiments,
      topLevelAwait: true,
    };
    
    // Configure watch options to prevent EMFILE errors
    if (dev && !isServer) {
      config.watchOptions = {
        ignored: [
          '**/node_modules',
          '**/.git',
          '**/.next',
          '**/dist',
          '**/build',
          '**/coverage',
          '**/logs',
          '**/temp_files',
          '**/backups',
          '**/quarantine',
          '**/system_backups',
          '**/monitoring',
          '**/reports',
          '**/scripts',
          '**/docs',
          '**/extensions',
          '**/headers',
          '**/models',
          '**/plugins',
          '/media/zeus/Development10/KIRO/**',
        ],
        aggregateTimeout: 300,
        poll: 1000, // Use polling instead of file system events
      };
    }
    
    return config;
  },
  
  // Add transpilation for problematic packages
  transpilePackages: ['@mui/material', '@mui/system', '@mui/utils', '@copilotkit/react-textarea', 'lucide-react'],

  // Fail fast if any static generation step hangs
  staticPageGenerationTimeout: 60,

  // API proxying is handled by the catch-all route in src/app/api/[...path]/route.ts
  // Remove rewrite rules to avoid conflicts with custom API route implementations
};

module.exports = withBundleAnalyzer(nextConfig);
