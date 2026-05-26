import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    // e2e/ 下是 Playwright 用例,需排除以免被 vitest 误收(详见 design/12 §2)
    exclude: ['node_modules/**', 'tests/e2e/**', 'dist/**', '.cache/**'],
  },
})
