import { defineConfig } from 'vitest';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'test-results/',
        'coverage/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/coverage/**',
        '**/dist/**',
        '**/test/**',
        '**/__tests__/**',
        '**/*.stories.{js,jsx,ts,tsx}',
        '**/mocks/**',
      ],
      thresholds: {
        global: {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85,
        },
        'src/components/task-management/**/*.{js,jsx,ts,tsx}': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90,
        },
        'src/components/memory/**/*.{js,jsx,ts,tsx}': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90,
        },
        'src/components/ui/**/*.{js,jsx,ts,tsx}': {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85,
        },
      },
      clean: true,
      cleanOnRerun: true,
    },
    include: [
      'src/**/*.{test,spec}.{js,jsx,ts,tsx}',
      'src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    ],
    exclude: [
      'node_modules/',
      'test-results/',
      'coverage/',
      'dist/',
      '**/*.config.*',
      '**/*.stories.{js,jsx,ts,tsx}',
      'src/**/__tests__/e2e/**',
      'src/**/__tests__/cross-browser/**',
      'src/**/__tests__/performance/**',
      'src/**/__tests__/visual/**',
      'src/**/__tests__/security/**',
      'src/**/__tests__/mocks/**',
      'src/lib/__tests__/accessibility-test-utils.ts',
      'src/lib/__tests__/test-utils.tsx',
      'src/lib/__tests__/testing-helpers.tsx',
      'src/components/performance-optimization/tests/integration.test.ts',
    ],
    testTimeout: 10000,
    hookTimeout: 10000,
    isolate: true,
    pool: 'threads',
    reporters: ['verbose', 'json', 'html'],
    outputFile: {
      json: './test-results/vitest-results.json',
      html: './test-results/vitest-report/index.html',
    },
    environmentOptions: {
      jsdom: {
        resources: 'usable',
        pretendToBeVisual: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/lib': path.resolve(__dirname, './src/lib'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/store': path.resolve(__dirname, './src/store'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/__tests__': path.resolve(__dirname, './src/__tests__'),
    },
  },
  define: {
    'process.env.NODE_ENV': '"test"',
    'process.env.NEXT_PUBLIC_APP_ENV': '"test"',
  },
});
