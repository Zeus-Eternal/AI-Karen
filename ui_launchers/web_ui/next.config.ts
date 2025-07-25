import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
    ],
  },
  
  // Environment variables configuration
  env: {
    KAREN_BACKEND_URL: process.env.KAREN_BACKEND_URL || 'http://localhost:8000',
    KAREN_API_TIMEOUT: process.env.KAREN_API_TIMEOUT || '30000',
    KAREN_API_MAX_RETRIES: process.env.KAREN_API_MAX_RETRIES || '3',
    KAREN_API_RETRY_DELAY: process.env.KAREN_API_RETRY_DELAY || '1000',
    KAREN_API_CACHE_TTL: process.env.KAREN_API_CACHE_TTL || '300000',
    KAREN_DEBUG_LOGGING: process.env.KAREN_DEBUG_LOGGING || 'false',
    KAREN_ENABLE_REQUEST_LOGGING: process.env.KAREN_ENABLE_REQUEST_LOGGING || 'false',
    KAREN_ENABLE_PERFORMANCE_MONITORING: process.env.KAREN_ENABLE_PERFORMANCE_MONITORING || 'false',
    KAREN_LOG_LEVEL: process.env.KAREN_LOG_LEVEL || 'info',
    KAREN_ENABLE_PLUGINS: process.env.KAREN_ENABLE_PLUGINS || 'true',
    KAREN_ENABLE_MEMORY: process.env.KAREN_ENABLE_MEMORY || 'true',
    KAREN_ENABLE_EXPERIMENTAL_FEATURES: process.env.KAREN_ENABLE_EXPERIMENTAL_FEATURES || 'false',
    KAREN_HEALTH_CHECK_INTERVAL: process.env.KAREN_HEALTH_CHECK_INTERVAL || '30000',
    KAREN_HEALTH_CHECK_TIMEOUT: process.env.KAREN_HEALTH_CHECK_TIMEOUT || '5000',
    KAREN_ENABLE_HEALTH_CHECKS: process.env.KAREN_ENABLE_HEALTH_CHECKS || 'true',
  },

  // Headers configuration for CORS and security
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: process.env.KAREN_CORS_ORIGINS || 'http://localhost:9002',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization, X-Requested-With, X-Web-UI-Compatible',
          },
          {
            key: 'Access-Control-Allow-Credentials',
            value: 'true',
          },
        ],
      },
    ];
  },

  // Rewrites for API proxy (optional - for development)
  async rewrites() {
    const backendUrl = process.env.KAREN_BACKEND_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/backend/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },

  // Experimental features
  // Next.js 15 moved `experimental.serverComponentsExternalPackages`
  // to a top-level `serverExternalPackages` option.
  // Update config accordingly.
  serverExternalPackages: [],

  // Output configuration
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,

  // Compression
  compress: true,

  // Power by header
  poweredByHeader: false,

  // Generate build ID
  generateBuildId: async () => {
    return `karen-web-ui-${Date.now()}`;
  },
};

export default nextConfig;
