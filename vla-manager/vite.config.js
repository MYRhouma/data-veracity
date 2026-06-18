import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const BACKEND_URL = process.env.VLA_MANAGER_BACKEND_URL || 'http://localhost:9090'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false
      }
    }
  }
})
