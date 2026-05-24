import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const BACKEND = process.env.VITE_API_TARGET || 'http://127.0.0.1:18080'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 15173,
    strictPort: true,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true, ws: true },
      '/assets': { target: BACKEND, changeOrigin: true },
    },
  },
})
