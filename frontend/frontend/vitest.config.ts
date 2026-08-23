import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [
    react(),
  ],

  test: {
    environment: "jsdom",

    globals: true,

    setupFiles: [
      "../tests/frontend/setup.ts",
    ],

    css: true,

    clearMocks: true,

    restoreMocks: true,

    include: [
      "../tests/frontend/**/*.{test,spec}.{ts,tsx}",
    ],
  },

  server: {
    host: "127.0.0.1",
    port: 5173,

    proxy: {
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

      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});