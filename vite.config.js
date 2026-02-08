import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: true,           // 需要在同網段測試可保留，純本機可省略
    proxy: {
      // 轉發 API 到 Flask
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        // 不要 rewrite，後端路徑本來就有 /api
      },
      // 轉發靜態圖片到 Flask 的 /static
      '/static': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
