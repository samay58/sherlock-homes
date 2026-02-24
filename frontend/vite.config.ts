import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const apiTarget = process.env.VITE_API_TARGET ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/health': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/ping': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/listings': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/matches': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/criteria': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/feedback': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/admin': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/ingestion': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/openapi.json': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
})
