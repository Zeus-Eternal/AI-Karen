import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Enable React strict mode for better error handling
  reactStrictMode: true,
  
  // Enable experimental features for better performance
  experimental: {
    // Optimize CSS
    optimizeCss: true,
  },
  
  // Configure server external packages
  serverExternalPackages: ['ag-grid-community', 'ag-grid-react'],
  
  // Configure transpilation for specific packages
  transpilePackages: [],
  
  // Configure webpack for better bundle optimization
  webpack: (config, { isServer }) => {
    // Optimize bundle splitting
    config.optimization.splitChunks = {
      chunks: 'all',
      cacheGroups: {
        default: {
          minChunks: 2,
          priority: -20,
          reuseExistingChunk: true,
        },
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: -10,
          chunks: 'all',
        },
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react',
          priority: 20,
          chunks: 'all',
        },
        ui: {
          test: /[\\/]node_modules[\\/](@radix-ui|lucide-react)[\\/]/,
          name: 'ui',
          priority: 30,
          chunks: 'all',
        },
        karen: {
          test: /[\\/]node_modules[\\/](ag-grid|framer-motion|zustand)[\\/]/,
          name: 'karen',
          priority: 40,
          chunks: 'all',
        },
      },
    };
    
    // Configure resolve aliases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': './src',
    };
    
    return config;
  },
  
  // Configure headers for security and performance
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
        ],
      },
    ];
  },
  
  // Configure redirects for SPA behavior
  async redirects() {
    return [
      // Add any necessary redirects here
    ];
  },
  
  // Configure image optimization
  images: {
    domains: [],
    formats: ['image/webp', 'image/avif'],
  },
  
  // Configure environment variables
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
};

export default nextConfig;