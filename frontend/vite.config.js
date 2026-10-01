import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The dev server proxies API and media requests to Django so the frontend can
// talk to the backend without CORS friction during development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})
