/// <reference types="./config/vitest.d.ts" />
import { defineConfig } from 'vitest/config'
import { resolve } from 'path'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    typecheck: {
      tsconfig: './tsconfig.vitest.json',
    },
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./config/test-setup.ts', './config/vitest.d.ts'],
    include: ['src/**/__tests__/**/*.{test,spec}.{js,ts,tsx}'],
    exclude: ['node_modules', '.next', 'dist'],
    testTimeout: 10000,
    hookTimeout: 10000,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      // Direct alias for clsx to bypass module resolution issues
      'clsx': resolve(__dirname, './config/mocks/clsx-mock.ts'),
    },
    // Optimize for dual-package modules and ESM compatibility
    conditions: ['module', 'import', 'default', 'types'],
    // Ensure proper resolution of ESM exports
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json'],
    // Add explicit resolution for problematic modules
    dedupe: ['clsx', 'tailwind-merge'],
  },
  define: {
    'process.env.NODE_ENV': '"test"',
  },
  optimizeDeps: {
    // Handle dual-package modules that might have ESM/CJS conflicts
    include: [
      '@vitejs/plugin-react',
      'react',
      'react-dom',
      'clsx',
      'tailwind-merge',
    ],
    // Force optimization for problematic packages
    force: true,
  },
  ssr: {
    // Configure SSR for proper ESM handling
    noExternal: [
      '@vitejs/plugin-react',
    ],
  },
})