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
      // =================================================

      "/auth": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      // =================================================
      // Project Control snapshot API
      //
      // IMPORTANT:
      // /project-control/projects is a React application
      // route and MUST NOT be proxied.
      //
      // Only the project-specific snapshot endpoint is
      // proxied:
      //
      // /project-control/projects/{project_id}
      // =================================================

      "^/project-control/projects/[^/]+$": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      // =================================================
      // Project Registry API
      //
      // D5.3 authoritative Project Registry endpoints:
      //
      // GET   /project-control/registry/projects
      // POST  /project-control/registry/projects
      // GET   /project-control/registry/projects/{id}
      // PATCH /project-control/registry/projects/{id}
      //
      // This is deliberately separate from the React route:
      //
      // /project-control/projects
      // =================================================

      "/project-control/registry": {
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
      // =================================================

      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});