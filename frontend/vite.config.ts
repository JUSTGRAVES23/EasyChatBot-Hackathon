import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [
    react(),
  ],

  server: {
    host: "127.0.0.1",
    port: 5173,

    proxy: {
      // =====================================================
      // Existing EasyChatBot backend APIs
      // =====================================================

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

      // =====================================================
      // API namespace
      //
      // Includes:
      // /api/privacy/governance/summary
      // /api/privacy/governance/status-chart
      // /api/privacy/governance/cases
      // /api/privacy/governance/cases/{case_id}
      //
      // Keep this generic so future platform APIs can use
      // the same backend boundary.
      // =====================================================

      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});