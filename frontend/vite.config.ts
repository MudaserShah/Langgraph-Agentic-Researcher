import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // "@/components/..." maps to "src/components/..."
      // This lets us use clean imports instead of ../../components/...
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    // Proxy API requests to the backend during development.
    // When the frontend calls "/api/research", Vite forwards it to
    // http://localhost:8002/research — no CORS issues in dev.
    // In production you'd configure your web server (nginx, etc.) instead.
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
