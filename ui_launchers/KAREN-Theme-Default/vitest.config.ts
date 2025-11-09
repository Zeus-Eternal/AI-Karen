/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  root: __dirname, // make resolution deterministic for the extension
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', '.next', 'dist', 'coverage'],
    setupFiles: [path.resolve(__dirname, 'vitest.setup.ts')], // use a root file
    typecheck: {
      tsconfig: path.resolve(__dirname, 'tsconfig.json'),
    },
    alias: {
      nodemailer: path.resolve(__dirname, 'stubs/nodemailer.ts'),
    },
    server: {
      deps: {
        inline: [
          '@mui/material',
          '@mui/system',
          '@mui/icons-material',
          '@mui/lab',
          '@mui/x-data-grid',
          '@emotion/react',
          '@emotion/styled',
          '@emotion/cache',
          '@emotion/serialize',
          '@emotion/utils',
          /^@mui\//,
          /^@emotion\//
        ]
      }
    },
    css: false,
    restoreMocks: true,
    clearMocks: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      all: false
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
});
