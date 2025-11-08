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
  
  // These are now top-level config options in Next.js 15
  skipTrailingSlashRedirect: true,
  skipMiddlewareUrlNormalize: true,
  
  // Disable static generation to avoid Html import issues
  output: 'standalone',
  

  
  // Cross-origin configuration handled in headers
  
  // Force Next.js to use this directory as the workspace root
  distDir: '.next',
  
  // Explicitly set the output file tracing root to prevent workspace detection issues
  outputFileTracingRoot: __dirname,
  
  // TypeScript configuration - disable for faster builds
  typescript: {
    // Skip type checking during build for speed
    ignoreBuildErrors: true,
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
  eslint: {
    // Skip ESLint during builds for speed
    ignoreDuringBuilds: true,
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
      // Fix refractor/core module resolution for older react-syntax-highlighter versions
      'refractor/core': require.resolve('refractor'),
      'refractor/core.js': require.resolve('refractor'),
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
        }),
        // Ignore problematic Html imports from next/document
        new webpack.IgnorePlugin({
          resourceRegExp: /next\/document/,
        }),
        // Ignore Html component specifically
        new webpack.IgnorePlugin({
          resourceRegExp: /Html/,
          contextRegExp: /next/,
        })
      );

      // Add fallbacks for missing refractor modules
      config.resolve.fallback = {
        ...config.resolve.fallback,
        'refractor/abap': false,
        'refractor/abnf': false,
        'refractor/actionscript': false,
        'refractor/ada': false,
        'refractor/agda': false,
        'refractor/al': false,
        'refractor/antlr4': false,
        'refractor/apache': false,
        'refractor/apex': false,
        'refractor/apl': false,
        'refractor/applescript': false,
        'refractor/aql': false,
        'refractor/arduino': false,
        'refractor/arff': false,
        'refractor/asciidoc': false,
        'refractor/aspnet': false,
        'refractor/asm6502': false,
        'refractor/autohotkey': false,
        'refractor/autoit': false,
        'refractor/bash': false,
        'refractor/basic': false,
        'refractor/batch': false,
        'refractor/bbcode': false,
        'refractor/birb': false,
        'refractor/bison': false,
        'refractor/bnf': false,
        'refractor/brainfuck': false,
        'refractor/brightscript': false,
        'refractor/bro': false,
        'refractor/bsl': false,
        'refractor/c': false,
        'refractor/clike': false,
        'refractor/cmake': false,
        'refractor/cobol': false,
        'refractor/coffeescript': false,
        'refractor/concurnas': false,
        'refractor/cpp': false,
        'refractor/crystal': false,
        'refractor/csharp': false,
        'refractor/csp': false,
        'refractor/css': false,
        'refractor/cypher': false,
        'refractor/d': false,
        'refractor/dart': false,
        'refractor/dataweave': false,
        'refractor/dax': false,
        'refractor/dhall': false,
        'refractor/diff': false,
        'refractor/django': false,
        'refractor/dns-zone-file': false,
        'refractor/docker': false,
        'refractor/dot': false,
        'refractor/ebnf': false,
        'refractor/editorconfig': false,
        'refractor/eiffel': false,
        'refractor/ejs': false,
        'refractor/elixir': false,
        'refractor/elm': false,
        'refractor/erb': false,
        'refractor/erlang': false,
        'refractor/etlua': false,
        'refractor/excel-formula': false,
        'refractor/factor': false,
        'refractor/false': false,
        'refractor/firestore-security-rules': false,
        'refractor/flow': false,
        'refractor/fortran': false,
        'refractor/fsharp': false,
        'refractor/ftl': false,
        'refractor/gcode': false,
        'refractor/gdscript': false,
        'refractor/gedcom': false,
        'refractor/gherkin': false,
        'refractor/git': false,
        'refractor/glsl': false,
        'refractor/gml': false,
        'refractor/go': false,
        'refractor/graphql': false,
        'refractor/groovy': false,
        'refractor/haml': false,
        'refractor/handlebars': false,
        'refractor/haskell': false,
        'refractor/haxe': false,
        'refractor/hcl': false,
        'refractor/hlsl': false,
        'refractor/hpkp': false,
        'refractor/hsts': false,
        'refractor/http': false,
        'refractor/ichigojam': false,
        'refractor/icon': false,
        'refractor/icu-message-format': false,
        'refractor/idris': false,
        'refractor/ignore': false,
        'refractor/inform7': false,
        'refractor/ini': false,
        'refractor/io': false,
        'refractor/j': false,
        'refractor/java': false,
        'refractor/javascript': false,
        'refractor/jexl': false,
        'refractor/jolie': false,
        'refractor/jq': false,
        'refractor/jsdoc': false,
        'refractor/js-extras': false,
        'refractor/json': false,
        'refractor/json5': false,
        'refractor/jsonp': false,
        'refractor/jsstacktrace': false,
        'refractor/js-templates': false,
        'refractor/julia': false,
        'refractor/keyman': false,
        'refractor/kotlin': false,
        'refractor/kumir': false,
        'refractor/latex': false,
        'refractor/latte': false,
        'refractor/less': false,
        'refractor/lilypond': false,
        'refractor/liquid': false,
        'refractor/lisp': false,
        'refractor/livescript': false,
        'refractor/llvm': false,
        'refractor/log': false,
        'refractor/lolcode': false,
        'refractor/lua': false,
        'refractor/makefile': false,
        'refractor/markdown': false,
        'refractor/markup': false,
        'refractor/markup-templating': false,
        'refractor/matlab': false,
        'refractor/mel': false,
        'refractor/mizar': false,
        'refractor/mongodb': false,
        'refractor/monkey': false,
        'refractor/moonscript': false,
        'refractor/n1ql': false,
        'refractor/n4js': false,
        'refractor/nand2tetris-hdl': false,
        'refractor/naniscript': false,
        'refractor/nasm': false,
        'refractor/neon': false,
        'refractor/nginx': false,
        'refractor/nim': false,
        'refractor/nix': false,
        'refractor/nsis': false,
        'refractor/objectivec': false,
        'refractor/ocaml': false,
        'refractor/opencl': false,
        'refractor/openqasm': false,
        'refractor/oz': false,
        'refractor/parigp': false,
        'refractor/parser': false,
        'refractor/pascal': false,
        'refractor/pascaligo': false,
        'refractor/pcaxis': false,
        'refractor/peoplecode': false,
        'refractor/perl': false,
        'refractor/php': false,
        'refractor/phpdoc': false,
        'refractor/php-extras': false,
        'refractor/plsql': false,
        'refractor/powerquery': false,
        'refractor/powershell': false,
        'refractor/processing': false,
        'refractor/prolog': false,
        'refractor/properties': false,
        'refractor/protobuf': false,
        'refractor/pug': false,
        'refractor/puppet': false,
        'refractor/pure': false,
        'refractor/purebasic': false,
        'refractor/purescript': false,
        'refractor/python': false,
        'refractor/q': false,
        'refractor/qml': false,
        'refractor/qore': false,
        'refractor/r': false,
        'refractor/racket': false,
        'refractor/reason': false,
        'refractor/regex': false,
        'refractor/renpy': false,
        'refractor/rest': false,
        'refractor/rip': false,
        'refractor/roboconf': false,
        'refractor/robotframework': false,
        'refractor/ruby': false,
        'refractor/rust': false,
        'refractor/sas': false,
        'refractor/sass': false,
        'refractor/scala': false,
        'refractor/scheme': false,
        'refractor/scss': false,
        'refractor/shell-session': false,
        'refractor/smali': false,
        'refractor/smalltalk': false,
        'refractor/smarty': false,
        'refractor/sml': false,
        'refractor/solidity': false,
        'refractor/solution-file': false,
        'refractor/soy': false,
        'refractor/sparql': false,
        'refractor/splunk-spl': false,
        'refractor/sqf': false,
        'refractor/sql': false,
        'refractor/squirrel': false,
        'refractor/stan': false,
        'refractor/stylus': false,
        'refractor/swift': false,
        'refractor/systemd': false,
        'refractor/t4-cs': false,
        'refractor/t4-templating': false,
        'refractor/t4-vb': false,
        'refractor/tap': false,
        'refractor/tcl': false,
        'refractor/textile': false,
        'refractor/toml': false,
        'refractor/tsx': false,
        'refractor/tt2': false,
        'refractor/turtle': false,
        'refractor/twig': false,
        'refractor/typescript': false,
        'refractor/typoscript': false,
        'refractor/unrealscript': false,
        'refractor/uri': false,
        'refractor/v': false,
        'refractor/vala': false,
        'refractor/vbnet': false,
        'refractor/velocity': false,
        'refractor/verilog': false,
        'refractor/vhdl': false,
        'refractor/vim': false,
        'refractor/visual-basic': false,
        'refractor/warpscript': false,
        'refractor/wasm': false,
        'refractor/wiki': false,
        'refractor/wolfram': false,
        'refractor/xeora': false,
        'refractor/xml-doc': false,
        'refractor/xojo': false,
        'refractor/xquery': false,
        'refractor/yaml': false,
        'refractor/yang': false,
        'refractor/zig': false,
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

    // Let Next.js handle minification automatically

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

      // Tree shaking optimization - removed problematic aliases

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

      // Next.js already handles CSS extraction/minification; rely on built-in pipeline
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
  
  // Disable static generation for error pages
  // experimental: {
  //   staticGenerationAsyncStorage: false,
  //   staticGenerationBailout: 'force-static',
  // },
  
  // Skip static generation for problematic pages during build
  // experimental: {
  //   skipTrailingSlashRedirect: true,
  //   skipMiddlewareUrlNormalize: true,
  // },
  
  // Disable static optimization for error pages to avoid Html import issues
  generateBuildId: async () => {
    return 'build-' + Date.now();
  },

  // API proxying is handled by the catch-all route in src/app/api/[...path]/route.ts
  // Remove rewrite rules to avoid conflicts with custom API route implementations
};

module.exports = withBundleAnalyzer(nextConfig);
