import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In sviluppo /api/v2 è inoltrato al backend FastAPI (uvicorn su :8000); in produzione (Vercel) è same-origin.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:8000' } },
})
