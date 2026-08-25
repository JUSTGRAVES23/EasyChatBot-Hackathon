/// <reference types="vitest/config" />

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default defineConfig({
  plugins: [
    react(),
  ],

  // =====================================================
  // Vitest
  // =====================================================

  test: {
    environment: "jsdom",
    globals: true,

    include: [
      "../tests/frontend/**/*.{test,spec}.{ts,tsx}",
    ],

    setupFiles: [
      "./vitest.setup.ts",
    ],
  },

  // =====================================================
  // Module resolution
  // =====================================================

  resolve: {
    alias: {
      react: resolve(
        __dirname,
        "node_modules/react",
      ),

      "react-dom": resolve(
        __dirname,
        "node_modules/react-dom",
      ),

      "@testing-library/react": resolve(
        __dirname,
        "node_modules/@testing-library/react",
      ),

      "@testing-library/jest-dom": resolve(
        __dirname,
        "node_modules/@testing-library/jest-dom",
      ),
    },
  },

  // =====================================================
  // Vite development server
  // =====================================================

  server: {
    host: "127.0.0.1",
    port: 5173,

    fs: {
      allow: [
        "..",
      ],
    },

    proxy: {
      // =================================================
      // Existing EasyChatBot backend APIs
      // =================================================

      "/operations/governance": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      "/operations-center/dashboard": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      "/controls": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      "/governance": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      // =================================================
      // API boundary
      //
      // Includes:
      //
      // /api/privacy/governance/summary
      // /api/privacy/governance/status-chart
      // /api/privacy/governance/cases
      // /api/privacy/governance/cases/{case_id}
      //
      // =================================================

      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});