import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In production the SPA and API share an origin (Nginx proxies /api and /ws).
// The dev server mirrors that by proxying to a local API; override the target
// with VITE_DEV_API_TARGET if the API runs elsewhere.
const devApiTarget = process.env.VITE_DEV_API_TARGET || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': { target: devApiTarget, changeOrigin: true },
      '/ws': { target: devApiTarget, ws: true, changeOrigin: true },
      '/health': { target: devApiTarget, changeOrigin: true },
      '/metrics': { target: devApiTarget, changeOrigin: true },
    },
  },
  preview: { port: 5173, host: true },
});
