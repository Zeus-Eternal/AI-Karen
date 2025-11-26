import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import { createRequire } from 'module';
import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'fs';

const require = createRequire(import.meta.url);
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const projectRoot = resolve(__dirname, '../..');
const permissionsCandidates = [
  process.env.PERMISSIONS_CONFIG_PATH,
  resolve(projectRoot, 'config', 'permissions.json'),
  resolve(process.cwd(), 'config/permissions.json'),
  resolve('/', 'config', 'permissions.json'),
];

let baselinePermissionsPayload = '{}';
for (const candidate of permissionsCandidates) {
  if (!candidate) continue;
  try {
    baselinePermissionsPayload = readFileSync(candidate, 'utf8');
    break;
  } catch (error) {
    console.warn(
      `Failed to read permissions config at ${candidate}; trying next location.`,
      error
    );
  }
}

const envOverridePermissions =
  typeof process.env.NEXT_PUBLIC_PERMISSIONS_CONFIG === 'string' &&
  process.env.NEXT_PUBLIC_PERMISSIONS_CONFIG.trim().length > 0
    ? process.env.NEXT_PUBLIC_PERMISSIONS_CONFIG
    : null;
const resolvedPermissionsPayload = envOverridePermissions ?? baselinePermissionsPayload;

let hasCritters = true;
try {
  require.resolve('next/dist/compiled/critters');
} catch (error) {
  console.warn('Critters module not found; disabling optimizeCss experiment.');
  hasCritters = false;
}

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
    optimizeCss: hasCritters,
    optimizePackageImports: ['lucide-react', 'date-fns', 'lodash'],
  },

  env: {
    NEXT_PUBLIC_PERMISSIONS_CONFIG: resolvedPermissionsPayload,
    NEXT_PUBLIC_BASELINE_PERMISSIONS_CONFIG: baselinePermissionsPayload,
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

  // Security and performance headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          // Security headers
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
          // Performance headers
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
        ],
      },
      // Cache static assets aggressively
      {
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      // Cache images
      {
        source: '/:path*.{jpg,jpeg,png,gif,webp,avif,svg,ico}',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      // Cache fonts
      {
        source: '/:path*.{woff,woff2,eot,ttf,otf}',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
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
      '@root-config': resolve(__dirname, '../../config'),
      '@root-config/permissions.json': resolve(__dirname, '../../config/permissions.json'),
    };

    // Ensure the server compiler emits a pages-manifest.json even when only the app router is used
    if (isServer) {
      const path = require('path');
      config.plugins = config.plugins || [];
      config.plugins.push(
        new (class EnsurePagesManifestPlugin {
          apply(compiler) {
            compiler.hooks.afterEmit.tap('EnsurePagesManifestPlugin', () => {
              const outputDir = compiler?.options?.output?.path;
              if (!outputDir) return;
              const manifestPath = path.join(outputDir, 'pages-manifest.json');
              try {
                if (!existsSync(manifestPath)) {
                  mkdirSync(path.dirname(manifestPath), { recursive: true });
                  writeFileSync(manifestPath, '{}');
                }
              } catch (err) {
                console.warn('Failed to ensure pages-manifest.json', err);
              }
            });
          }
        })()
      );
    }

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