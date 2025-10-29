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
  // Remove asset prefix that's causing MIME type issues
  // assetPrefix: process.env.NODE_ENV === 'development' ? 'http://localhost:8010' : '',
  
  // Explicitly set the root directory to prevent Next.js from looking at parent directories
  experimental: {
    // Other experimental features can go here
  },
  
  // Allow cross-origin requests from Docker container network
  allowedDevOrigins: ['172.21.0.12'],
  
  // Force Next.js to use this directory as the workspace root
  distDir: '.next',
  
  // Explicitly set the output file tracing root to prevent workspace detection issues
  outputFileTracingRoot: __dirname,
  
  // TypeScript configuration
  typescript: {
    // Enable type checking during build for better code quality
    ignoreBuildErrors: false,
  },

  // Font optimization is enabled by default in Next.js 15

  // Suppress hydration warnings in development
  reactStrictMode: false,
  
  // Force development mode settings
  ...(process.env.NODE_ENV === 'development' && {
    // Disable minification in development
    swcMinify: false,
    // Enable source maps
    productionBrowserSourceMaps: false,
    // Disable optimization
    optimizeFonts: false,
  }),

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
    // Fix chunk loading issues in development
    if (dev && !isServer) {
      config.output = {
        ...config.output,
        chunkFilename: 'static/chunks/[name].js',
        hotUpdateChunkFilename: 'static/webpack/[id].[fullhash].hot-update.js',
      };
    }
    
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
    config.resolve.alias = {
      ...config.resolve.alias,
      'lodash/debounce': require.resolve('lodash.debounce'),
      'lodash/throttle': require.resolve('lodash.throttle'),
    };
    
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

    // Bundle optimization for production
    if (!dev && !isServer) {
      // Optimize chunk splitting
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            // Vendor libraries
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              chunks: 'all',
              priority: 10,
              reuseExistingChunk: true,
            },
            // React and React DOM
            react: {
              test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
              name: 'react',
              chunks: 'all',
              priority: 20,
              reuseExistingChunk: true,
            },
            // UI libraries (Radix, Framer Motion, etc.)
            ui: {
              test: /[\\/]node_modules[\\/](@radix-ui|framer-motion|lucide-react)[\\/]/,
              name: 'ui-libs',
              chunks: 'all',
              priority: 15,
              reuseExistingChunk: true,
            },
            // Charts and data visualization
            charts: {
              test: /[\\/]node_modules[\\/](ag-charts|ag-grid|recharts)[\\/]/,
              name: 'charts',
              chunks: 'all',
              priority: 15,
              reuseExistingChunk: true,
            },
            // Utilities and smaller libraries
            utils: {
              test: /[\\/]node_modules[\\/](date-fns|clsx|class-variance-authority|tailwind-merge)[\\/]/,
              name: 'utils',
              chunks: 'all',
              priority: 12,
              reuseExistingChunk: true,
            },
            // Common chunks for frequently used modules
            common: {
              name: 'common',
              minChunks: 2,
              chunks: 'all',
              priority: 5,
              reuseExistingChunk: true,
              enforce: true,
            },
          },
        },
        // Enable module concatenation for better tree shaking
        concatenateModules: true,
        // Enable side effects optimization
        sideEffects: false,
      };

      // Tree shaking optimization
      config.resolve.alias = {
        ...config.resolve.alias,
        // Optimize lodash imports
        'lodash': 'lodash-es',
        // Remove date-fns alias as it's causing issues
      };

      // Add webpack plugins for optimization
      const webpack = require('webpack');
      
      config.plugins.push(
        // Ignore moment.js locales to reduce bundle size
        new webpack.IgnorePlugin({
          resourceRegExp: /^\.\/locale$/,
          contextRegExp: /moment$/,
        }),
        // Define environment variables for dead code elimination
        new webpack.DefinePlugin({
          'process.env.NODE_ENV': JSON.stringify('production'),
          __DEV__: false,
        })
      );

      // Next.js already handles CSS extraction/minification; rely on built-in pipeline
    }
    
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
