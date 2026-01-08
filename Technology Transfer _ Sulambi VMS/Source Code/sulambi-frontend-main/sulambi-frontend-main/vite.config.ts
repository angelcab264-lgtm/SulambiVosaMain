import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost',
    port: 5173,
  },
  base: '/', // Ensure base path is root for static assets
  build: {
    assetsDir: 'assets',
    // Ensure public assets are copied correctly
    copyPublicDir: true,
  },
})
