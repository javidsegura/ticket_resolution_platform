import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from "@tailwindcss/vite"
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load all env vars from env_config/synced (including non-VITE_ prefixed ones)
  const envDir = path.resolve(__dirname, 'env_config/synced')
  const env = loadEnv(mode === 'development' ? 'dev' : mode, envDir, '')
  
  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: "0.0.0.0",
      port: 5173,
    },
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    // Load .env files from custom directory (enables automatic VITE_* variable exposure)
    envDir: envDir,
    // Map the simple variable names from .env.dev to import.meta.env
    define: {
      'import.meta.env.apiKey': JSON.stringify(env.apiKey || ''),
      'import.meta.env.authDomain': JSON.stringify(env.authDomain || ''),
      'import.meta.env.projectId': JSON.stringify(env.projectId || ''),
      'import.meta.env.storageBucket': JSON.stringify(env.storageBucket || ''),
      'import.meta.env.messagingSenderId': JSON.stringify(env.messagingSenderId || ''),
      'import.meta.env.appId': JSON.stringify(env.appId || ''),
      'import.meta.env.measurementId': JSON.stringify(env.measurementId || ''),
    },
  }
})
