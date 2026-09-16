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
      "./tests/frontend/**/*.{test,spec}.{ts,tsx}",
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
      "@": resolve(__dirname, "."),

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
      // Authentication API
      //
      // IMPORTANT:
      // The browser never receives or stores the session ID.
      //
      // The existing backend authentication service creates
      // the HttpOnly easychatbot_session cookie.
      // =================================================

      "/auth": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      // =================================================
      // Project Control API
      //
      // IMPORTANT:
      // Do NOT proxy /project-control itself.
      //
      // /project-control is a React application route.
      //
      // The API client uses:
      // /project-control/projects/{project_id}
      //
      // Therefore only the API resource path is proxied.
      // =================================================

      "/project-control/projects": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

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
      // /api/operations-center/functionality-health
      // /api/operations-center/risk-intelligence
      //
      // =================================================

      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
