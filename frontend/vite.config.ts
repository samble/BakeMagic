import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The FastAPI backend has no /api prefix; the dev server forwards /api/* to it
// and strips the prefix, so the browser only ever talks to one origin (no CORS).
const backend = process.env.BAKEMAGIC_API ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backend,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  preview: {
    proxy: {
      '/api': {
        target: backend,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
