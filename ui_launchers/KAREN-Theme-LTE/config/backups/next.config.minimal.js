/** @type {import('next').NextConfig} */
const nextConfig = {
  // Remove asset prefix that's causing MIME type issues
  // assetPrefix: process.env.NODE_ENV === 'development' ? 'http://localhost:8010' : '',

  // Skip static generation for routes that use dynamic server features
  generateBuildId: async () => {
    return 'build-' + Date.now();
  },

  // Disable static generation
  output: 'standalone',

  // Explicitly set the root directory to prevent Next.js from looking at parent directories
  experimental: {
    // Simplified experimental configuration to avoid conflicts
    swcPlugins: [],
    forceSwcTransforms: true,
    optimizeCss: false,
    optimizePackageImports: ['lucide-react', 'date-fns', 'lodash'],
  },

  // These are now top-level config options in Next.js 15
  skipTrailingSlashRedirect: true,

  // Force Next.js to use this directory as the workspace root
  distDir: '.next',

  // TypeScript configuration - enable for production readiness
  typescript: {
    // Enable type checking during build for production readiness
    ignoreBuildErrors: false,
  },

  // Font optimization is enabled by default in Next.js 15

  // Suppress hydration warnings in development
  reactStrictMode: false,

  // Disable source maps for faster builds
  productionBrowserSourceMaps: false,

  // Enable compression
  compress: true,

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 31536000, // 1 year
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Ensure all pages have proper revalidate values
  async rewrites() {
    return [
      {
        source: '/:path*',
        destination: '/:path*',
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
        dns: false,
        pg: false,
      };
    }

    // Exclude server-only modules from client bundle
    if (!isServer) {
      config.externals = config.externals || [];
      config.externals.push('pg');
    }

    // Fix lodash module resolution for slate-react (used by CopilotKit)
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      // Fix refractor/core module resolution for older react-syntax-highlighter versions
      'refractor/core': 'refractor',
      'refractor/core.js': 'refractor',
      // Redirect problematic async imports to safe fallbacks
      'react-syntax-highlighter/dist/esm/async-languages/prism': false,
      'react-syntax-highlighter/dist/esm/prism-async-light': false,
    };

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

  // API proxying is handled by catch-all route in src/app/api/[...path]/route.ts
  // Remove rewrite rules to avoid conflicts with custom API route implementations
};

export default nextConfig;