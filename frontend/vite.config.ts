import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const configuredPort = Number(env.VITE_PORT || 5173)
  const port = Number.isInteger(configuredPort) ? configuredPort : 5173
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    server: {
      host: env.VITE_HOST || 'localhost',
      port,
      proxy: {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true
        },
        '/health': {
          target: apiProxyTarget,
          changeOrigin: true
        }
      }
    }
  }
})
