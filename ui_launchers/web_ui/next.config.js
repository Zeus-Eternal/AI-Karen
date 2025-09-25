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
  experimental: {
    // Other experimental features can go here
  },
  
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
