import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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
    swcPlugins: [],
    forceSwcTransforms: true,
  },

  // Add turbopack config to silence the warning
  turbopack: {},

  // These are now top-level config options in Next.js 15
  skipTrailingSlashRedirect: true,

  // Cross-origin configuration handled in headers

  // Force Next.js to use this directory as the workspace root
  distDir: '.next',

  // Explicitly set the output file tracing root to prevent workspace detection issues
  outputFileTracingRoot: __dirname,

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

  // Performance optimizations - swcMinify and optimizeFonts are now default in Next.js 15

  // Compiler optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // ESLint configuration - disable for faster builds
  // Note: eslint config moved to .eslintrc files

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
      // Fix refractor/core module resolution for older react-syntax-highlighter versions
      'refractor/core': 'refractor',
      'refractor/core.js': 'refractor',
      // Redirect problematic async imports to safe fallbacks
      'react-syntax-highlighter/dist/esm/async-languages/prism': false,
      'react-syntax-highlighter/dist/esm/prism-async-light': false,
    };

    // Fix react-syntax-highlighter refractor language imports
    if (!isServer) {
      // Add webpack plugin to ignore missing refractor language modules
      const webpack = require('webpack');
      config.plugins = config.plugins || [];
      config.plugins.push(
        new webpack.IgnorePlugin({
          resourceRegExp: /^refractor\/lang-/,
        }),
        new webpack.IgnorePlugin({
          resourceRegExp: /^refractor\/[a-z]+$/,
          contextRegExp: /react-syntax-highlighter/,
        }),
        // Ignore the async language loader entirely
        new webpack.IgnorePlugin({
          resourceRegExp: /async-languages/,
          contextRegExp: /react-syntax-highlighter/,
        }),
        new webpack.IgnorePlugin({
          resourceRegExp: /prism-async/,
          contextRegExp: /react-syntax-highlighter/,
        })
      );

      // Add fallbacks for missing refractor modules - simplified
      config.resolve.fallback = {
        ...config.resolve.fallback,
        // Add only the most common refractor modules as fallbacks
        'refractor/javascript': false,
        'refractor/typescript': false,
        'refractor/python': false,
        'refractor/java': false,
        'refractor/css': false,
        'refractor/json': false,
        'refractor/markdown': false,
        'refractor/bash': false,
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

    // Bundle optimization for production
    if (!dev && !isServer) {
      // Optimize chunk splitting for better caching and loading performance
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          minSize: 20000,
          maxSize: 244000,
          cacheGroups: {
            // Framework chunk (React, Next.js)
            framework: {
              test: /[\\/]node_modules[\\/](react|react-dom|next)[\\/]/,
              name: 'framework',
              chunks: 'all',
              priority: 40,
              reuseExistingChunk: true,
              enforce: true,
            },
            // Large UI libraries
            ui: {
              test: /[\\/]node_modules[\\/](@radix-ui|framer-motion|lucide-react)[\\/]/,
              name: 'ui-libs',
              chunks: 'all',
              priority: 30,
              reuseExistingChunk: true,
              minSize: 10000,
            },
            // Charts and data visualization (lazy loaded)
            charts: {
              test: /[\\/]node_modules[\\/](ag-charts|ag-grid|recharts)[\\/]/,
              name: 'charts',
              chunks: 'async',
              priority: 25,
              reuseExistingChunk: true,
            },
            // Utilities and smaller libraries
            utils: {
              test: /[\\/]node_modules[\\/](date-fns|clsx|class-variance-authority|tailwind-merge|zod)[\\/]/,
              name: 'utils',
              chunks: 'all',
              priority: 20,
              reuseExistingChunk: true,
            },
            // Lodash utilities (tree-shakeable)
            lodash: {
              test: /[\\/]node_modules[\\/]lodash[\\/]/,
              name: 'lodash',
              chunks: 'all',
              priority: 15,
              reuseExistingChunk: true,
            },
            // Other vendor libraries
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              chunks: 'all',
              priority: 10,
              reuseExistingChunk: true,
              minSize: 30000,
            },
            // Common application code
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
        // Optimize module IDs for better caching
        moduleIds: 'deterministic',
        chunkIds: 'deterministic',
        // Enable side effects optimization
        sideEffects: false,
        // Let Next.js handle minification automatically
        minimize: true,
      };

      // Enable advanced optimizations
      config.optimization.usedExports = true;
      config.optimization.providedExports = true;
      config.optimization.innerGraph = true;

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
    }

    // Development optimizations
    if (dev) {
      // Faster rebuilds in development
      config.cache = {
        type: 'filesystem',
        buildDependencies: {
          config: [__filename],
        },
      };

      // Configure watch options to prevent EMFILE errors
      if (!isServer) {
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

export default withBundleAnalyzer(nextConfig);