import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

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
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/listings': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/matches': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/criteria': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/feedback': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
