/// <reference types="vitest" />
import { defineConfig } from "vitest/config";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  root: rootDir, // make resolution deterministic for the extension
  test: {
    globals: true,
    environment: "jsdom",
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    exclude: ["node_modules", ".next", "dist", "coverage"],
    setupFiles: [resolve(rootDir, "vitest.setup.ts")], // use a root file
    typecheck: {
      tsconfig: resolve(rootDir, "tsconfig.json"),
    },
    deps: {
      inline: [
        "@mui/material",
        "@mui/system",
        "@mui/icons-material",
        "@mui/lab",
        "@mui/x-data-grid",
        "@emotion/react",
        "@emotion/styled",
        "@emotion/cache",
        "@emotion/serialize",
        "@emotion/utils",
        /^@mui\//,
        /^@emotion\//,
      ],
    },
    css: false,
    restoreMocks: true,
    clearMocks: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      all: false,
    },
  },
  resolve: {
    alias: {
      "@": resolve(rootDir, "src"),
      nodemailer: resolve(rootDir, "stubs/nodemailer.ts"),
    },
  },
});
