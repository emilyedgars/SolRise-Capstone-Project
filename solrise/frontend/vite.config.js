import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// ─────────────────────────────────────────────────────────
//  DRAFT SWITCHER
//  Draft 1 — Atlantic Digital (original):  ENTRY = 'src/main.jsx'
//  Draft 2 — SolRise (new brand):          ENTRY = 'src/main2.jsx'
// ─────────────────────────────────────────────────────────
const ENTRY = 'src/main2.jsx'  // ← change to 'src/main.jsx' for Atlantic Digital draft

export default defineConfig({
    plugins: [react()],
    build: { rollupOptions: { input: ENTRY } },
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:5001',
                changeOrigin: true,
            }
        }
    }
})
