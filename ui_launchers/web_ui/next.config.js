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
    // Ignore TypeScript errors during build (for problematic dependencies)
    ignoreBuildErrors: false,
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
};

module.exports = withBundleAnalyzer(nextConfig);
