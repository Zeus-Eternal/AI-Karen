/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import { resolve } from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    typecheck: {
      tsconfig: './tsconfig.json',
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
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
});