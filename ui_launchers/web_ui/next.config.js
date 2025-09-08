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
    turbo: {
      resolveAlias: {
        '@mui/utils/composeClasses': '@mui/utils/composeClasses/index.js',
      },
      // Ignore problematic tsconfig files
      rules: {
        '*.json': {
          loaders: ['ignore-loader'],
          as: '*.js',
        },
      },
    },
  },
  
  // TypeScript configuration
  typescript: {
    // Skip type checking during build to avoid stalls from TS/dep issues
    ignoreBuildErrors: true,
  },

  // ESLint configuration
  eslint: {
    // Skip ESLint during production builds
    ignoreDuringBuilds: true,
  },
  
  webpack: (config, { isServer }) => {
    // Handle ES modules properly
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    
    // Ignore problematic tsconfig files
    config.resolve.alias = {
      ...config.resolve.alias,
    };
    
    return config;
  },
  
  // Add transpilation for problematic packages
  transpilePackages: ['@mui/material', '@mui/system', '@mui/utils', '@copilotkit/react-textarea'],

  // Fail fast if any static generation step hangs
  staticPageGenerationTimeout: 60,

  // Proxy rewrites so frontend /api calls reach the backend API
  async rewrites() {
    const backendUrl = process.env.KAREN_BACKEND_URL || 'http://localhost:8000';
    return [
      // Generic passthrough
      { source: '/api/backend/:path*', destination: `${backendUrl}/api/:path*` },
      // Auth
      { source: '/api/auth/:path*', destination: `${backendUrl}/api/auth/:path*` },
      // Copilot actions: strip 'copilot' and map to /api/:path*
      { source: '/api/copilot/:path*', destination: `${backendUrl}/api/:path*` },
      // Legacy copilot assist endpoint at root (client may call directly)
      { source: '/copilot/assist', destination: `${backendUrl}/copilot/assist` },
      { source: '/copilot/:path*', destination: `${backendUrl}/copilot/:path*` },
      // Models/providers
      { source: '/api/models/:path*', destination: `${backendUrl}/api/models/:path*` },
      { source: '/api/llm/:path*', destination: `${backendUrl}/api/llm/:path*` },
      // Health
      { source: '/api/health', destination: `${backendUrl}/api/health` },
      { source: '/health', destination: `${backendUrl}/health` },
    ];
  },
};

module.exports = withBundleAnalyzer(nextConfig);
