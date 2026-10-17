import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// Dev proxy target. Not prefixed with VITE_, so it never reaches the bundle.
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:8106';

// The two API routes mirror the nginx image: /api/v1/* keeps its path, /api/health maps to /health.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/v1': { target: apiTarget, changeOrigin: true },
      '/api/health': {
        target: apiTarget,
        changeOrigin: true,
        rewrite: () => '/health',
      },
    },
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['src/test/setup.ts'],
  },
});
